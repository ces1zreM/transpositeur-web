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

# Configuration CORS pour Render et local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION DES CHEMINS ---
current_dir = os.path.dirname(os.path.abspath(__file__))

# Dossiers temporaires (Chemins relatifs pour s'adapter partout)
UPLOAD_DIR = os.path.join(current_dir, "temp_music")
OUTPUT_DIR = os.path.join(current_dir, "output_music")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Détection automatique de l'environnement (Linux/Render vs Windows/Local)
if os.name == 'nt':  # Windows
    AUDIVERIS_BIN = r"C:\Program Files\Audiveris\Audiveris.exe"
    IS_LINUX = False
else:  # Linux (Render)
    AUDIVERIS_BIN = "/app/Audiveris.jar"
    IS_LINUX = True

# --- DISPOSITIF 1 : Transposition ---
@app.post("/transpose")
async def transpose_file(
        file: UploadFile = File(...),
        semitones: int = Form(...),
        clef: str = Form(...)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"📥 Fichier reçu pour traitement : {file_path}")
    print(f"⚙️ Paramètres -> Transposition: {semitones} demi-tons | Clé forcée: {clef}")

    try:
        score = converter.parse(file_path)

        if semitones != 0:
            score = score.transpose(interval.Interval(semitones))

        if clef != "auto":
            for part in score.getElementsByClass('Part'):
                for measure in part.getElementsByClass('Measure'):
                    existing_clefs = measure.getElementsByClass(music21_clef.Clef)

                    if clef == "Treble": new_clef = music21_clef.TrebleClef()
                    elif clef == "Bass": new_clef = music21_clef.BassClef()
                    elif clef == "Soprano": new_clef = music21_clef.SopranoClef()
                    elif clef == "Alto": new_clef = music21_clef.AltoClef()
                    elif clef == "Tenor": new_clef = music21_clef.TenorClef()

                    if existing_clefs:
                        measure.replace(existing_clefs[0], new_clef)
                    elif measure.number in [0, 1]:
                        measure.insert(0, new_clef)

        xml_data = score.write('musicxml')
        with open(xml_data, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        try: os.remove(xml_data)
        except: pass

        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        print(f"❌ Erreur lors de la transformation : {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- DISPOSITIF 2 : Conversion PDF (Audiveris) ---
@app.post("/convert-pdf")
async def convert_pdf_to_mxl(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Le fichier doit être un PDF."})

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"📸 Vrai Scan PDF reçu pour numérisation Audiveris OMR : {pdf_path}")

    try:
        output_name = file.filename.rsplit('.', 1)[0]
        
        # Commande adaptée selon l'OS (Windows .exe ou Linux .jar)
        if IS_LINUX:
            command = ["java", "-Djava.awt.headless=true", "-jar", AUDIVERIS_BIN, "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path]
        else:
            command = [AUDIVERIS_BIN, "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path]

        print("🤖 Audiveris calcule la partition en arrière-plan...")
        result = subprocess.run(command, capture_output=True, text=True)

        # RECHERCHE INTELLIGENTE (Ta logique idéale)
        fichiers_trouves = glob.glob(os.path.join(OUTPUT_DIR, f"{output_name}*.*"))
        fichier_cible = next((f for f in fichiers_trouves if f.lower().endswith(('.mxl', '.musicxml'))), None)

        if fichier_cible and os.path.exists(fichier_cible):
            print(f"✅ Partition détectée et récupérée : {fichier_cible}")
            score = converter.parse(fichier_cible)
            xml_data = score.write('musicxml')

            with open(xml_data, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            try: os.remove(xml_data)
            except: pass
            return Response(content=xml_content, media_type="application/xml")
        else:
            print(f"❌ Aucun fichier musical trouvé. Logs :\n{result.stderr}")
            return JSONResponse(status_code=500, content={"error": "Échec de l'analyse Audiveris (Fichier introuvable)."})

    except Exception as e:
        print(f"❌ Erreur critique du serveur OMR : {e}")
        return JSONResponse(status_code=500, content={"error": f"Erreur interne : {str(e)}"})

# --- SERVIR LE FRONTEND (Pour Render) ---
build_path = os.path.join(current_dir, "build")
if os.path.exists(build_path):
    app.mount("/", StaticFiles(directory=build_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Port dynamique pour Render, 8000 pour local
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
