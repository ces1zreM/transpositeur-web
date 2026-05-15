from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import subprocess
import glob
from music21 import converter, interval, clef as music21_clef

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION DES CHEMINS ---
current_dir = os.path.dirname(os.path.abspath(__file__))

# Dossiers pour les fichiers temporaires
UPLOAD_DIR = os.path.join(current_dir, "temp_music")
OUTPUT_DIR = os.path.join(current_dir, "output_music")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Détection de l'environnement et configuration Audiveris
if os.name == 'nt':  # Windows (Ton PC local)
    AUDIVERIS_BIN = r"C:\Program Files\Audiveris\Audiveris.exe"
    IS_LINUX = False
else:  # Linux (Serveur Render)
    # Chemin vers le dossier que tu vas créer dans ton projet
    AUDIVERIS_LIB_PATH = "/app/backend/audiveris_local/app/*"
    IS_LINUX = True


# --- DISPOSITIF 1 : Transposition (Fichiers déjà numériques) ---
@app.post("/transpose")
async def transpose_file(
        file: UploadFile = File(...),
        semitones: int = Form(...),
        clef: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        score = converter.parse(file_path)

        if semitones != 0:
            score = score.transpose(interval.Interval(semitones))

        if clef != "auto":
            for part in score.getElementsByClass('Part'):
                for measure in part.getElementsByClass('Measure'):
                    existing_clefs = measure.getElementsByClass(music21_clef.Clef)

                    if clef == "Treble":
                        new_clef = music21_clef.TrebleClef()
                    elif clef == "Bass":
                        new_clef = music21_clef.BassClef()
                    elif clef == "Soprano":
                        new_clef = music21_clef.SopranoClef()
                    elif clef == "Alto":
                        new_clef = music21_clef.AltoClef()
                    elif clef == "Tenor":
                        new_clef = music21_clef.TenorClef()

                    if existing_clefs:
                        measure.replace(existing_clefs[0], new_clef)
                    elif measure.number in [0, 1]:
                        measure.insert(0, new_clef)

        xml_data = score.write('musicxml')
        with open(xml_data, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        try:
            os.remove(xml_data)
        except:
            pass

        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- DISPOSITIF 2 : Conversion Scan PDF (Audiveris) ---
@app.post("/convert-pdf")
async def convert_pdf_to_mxl(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Le fichier doit être un PDF."})

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        output_name = file.filename.rsplit('.', 1)[0]

        if IS_LINUX:
            # Commande Linux : on appelle Java avec toutes les librairies du dossier app/
            command = [
                "java",
                "-Djava.awt.headless=true",
                "-cp", AUDIVERIS_LIB_PATH,
                "org.audiveris.audiveris.Audiveris",
                "-batch", "-transcribe", "-export",
                "-output", OUTPUT_DIR,
                pdf_path
            ]
        else:
            # Commande Windows locale
            command = [AUDIVERIS_BIN, "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path]

        print(f"🤖 Analyse Audiveris en cours pour : {file.filename}...")
        result = subprocess.run(command, capture_output=True, text=True)

        # Recherche du fichier généré (mxl ou musicxml)
        fichiers_trouves = glob.glob(os.path.join(OUTPUT_DIR, f"{output_name}*.*"))
        fichier_cible = next((f for f in fichiers_trouves if f.lower().endswith(('.mxl', '.musicxml'))), None)

        if fichier_cible and os.path.exists(fichier_cible):
            print(f"✅ Analyse réussie : {fichier_cible}")
            score = converter.parse(fichier_cible)
            xml_data = score.write('musicxml')

            with open(xml_data, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            try:
                os.remove(xml_data)
            except:
                pass
            return Response(content=xml_content, media_type="application/xml")
        else:
            print(f"❌ Erreur : Fichier non généré par Audiveris.\nLogs : {result.stderr}")
            return JSONResponse(status_code=500, content={"error": "Échec de l'analyse (Fichier introuvable)."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erreur OMR : {str(e)}"})


# --- SERVIR LE FRONTEND ---
# Assure-toi que ton dossier 'build' est bien à la racine ou dans backend/
build_path = os.path.join(os.path.dirname(current_dir), "build")
if os.path.exists(build_path):
    app.mount("/", StaticFiles(directory=build_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
