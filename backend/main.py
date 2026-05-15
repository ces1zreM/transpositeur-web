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

UPLOAD_DIR = os.path.join(current_dir, "temp_music")
OUTPUT_DIR = os.path.join(current_dir, "output_music")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Détection de l'environnement
if os.name == 'nt':  # Windows
    AUDIVERIS_BIN = r"C:\Program Files\Audiveris\Audiveris.exe"
    IS_LINUX = False
else:  # Linux (Render avec installation complète)
    # Chemin vers le script de lancement installé par le Dockerfile
    AUDIVERIS_BIN = "/app/AudiverisApp/bin/Audiveris" 
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
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- DISPOSITIF 2 : Conversion PDF (Audiveris) ---
@app.post("/convert-pdf")
async def convert_pdf_to_mxl(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Le fichier doit être un PDF."})

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        output_name = file.filename.rsplit('.', 1)[0]
        
        # Commande adaptée
        if IS_LINUX:
            # Sur Linux, on utilise le script de lancement avec l'option headless
            command = [AUDIVERIS_BIN, "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path]
            # Note: Le script 'Audiveris' sous Linux gère souvent déjà les arguments Java. 
            # Si besoin, on peut ajouter env={"JAVA_OPTS": "-Djava.awt.headless=true"} dans subprocess.run
        else:
            command = [AUDIVERIS_BIN, "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path]

        print(f"🤖 Lancement Audiveris sur : {pdf_path}")
        # On ajoute headless via les variables d'environnement pour Linux
        env = os.environ.copy()
        if IS_LINUX:
            env["JAVA_OPTS"] = "-Djava.awt.headless=true"

        result = subprocess.run(command, capture_output=True, text=True, env=env)

        # Recherche du fichier généré
        fichiers_trouves = glob.glob(os.path.join(OUTPUT_DIR, f"{output_name}*.*"))
        fichier_cible = next((f for f in fichiers_trouves if f.lower().endswith(('.mxl', '.musicxml'))), None)

        if fichier_cible and os.path.exists(fichier_cible):
            score = converter.parse(fichier_cible)
            xml_data = score.write('musicxml')

            with open(xml_data, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            try: os.remove(xml_data)
            except: pass
            return Response(content=xml_content, media_type="application/xml")
        else:
            print(f"❌ Erreur Audiveris. Logs :\n{result.stderr}")
            return JSONResponse(status_code=500, content={"error": "Échec de l'analyse Audiveris (Fichier non généré)."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erreur interne : {str(e)}"})

# --- SERVIR LE FRONTEND ---
build_path = os.path.join(current_dir, "build")
if os.path.exists(build_path):
    app.mount("/", StaticFiles(directory=build_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
