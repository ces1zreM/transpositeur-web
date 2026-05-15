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

# On autorise tout le monde pour éviter les blocages sur le serveur
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION DES CHEMINS RAILWAY ---
current_dir = os.path.dirname(os.path.abspath(__file__))

# Dossiers temporaires sur le serveur
UPLOAD_DIR = os.path.join(current_dir, "temp_music")
OUTPUT_DIR = os.path.join(current_dir, "output_music")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Le JAR d'Audiveris sera à la racine /app/ selon notre Dockerfile
AUDIVERIS_JAR = "/app/Audiveris.jar"


# --- DISPOSITIF 1 : TRANSPOSITION ---
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
        return Response(content=xml_content, media_type="application/xml")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- DISPOSITIF 2 : CONVERSION PDF (AUDIVERIS) ---
@app.post("/convert-pdf")
async def convert_pdf_to_mxl(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Le fichier doit être un PDF."})

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        output_name = file.filename.rsplit('.', 1)[0]

        # Commande Linux/Railway pour lancer le JAR Java
        command = [
            "java", "-Djava.awt.headless=true",
            "-jar", AUDIVERIS_JAR,
            "-batch", "-transcribe", "-export", "-output", OUTPUT_DIR, pdf_path
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        fichiers_trouves = glob.glob(os.path.join(OUTPUT_DIR, f"{output_name}*.*"))
        fichier_cible = next((f for f in fichiers_trouves if f.lower().endswith(('.mxl', '.musicxml'))), None)

        if fichier_cible:
            score = converter.parse(fichier_cible)
            xml_data = score.write('musicxml')
            with open(xml_data, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            return Response(content=xml_content, media_type="application/xml")
        else:
            return JSONResponse(status_code=500, content={"error": "Échec de l'analyse Audiveris"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- SERVIR LE FRONTEND (REACT BUILD) ---
build_path = os.path.join(current_dir, "build")
if os.path.exists(build_path):
    app.mount("/", StaticFiles(directory=build_path, html=True), name="static")

# --- LANCEMENT SERVEUR (PORT DYNAMIQUE) ---
if __name__ == "__main__":
    import uvicorn

    # Railway injecte la variable PORT, sinon on utilise 8080 par défaut
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)