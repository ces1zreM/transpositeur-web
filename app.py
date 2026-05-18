from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import subprocess

app = FastAPI()

AUDIVERIS_ROOT_DIR = "/app/audiveris_local"
UPLOAD_DIR = "/app/temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/omr")
async def process_pdf(file: UploadFile = File(...)):
    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Copie dans le répertoire d'Audiveris
        local_pdf = os.path.join(AUDIVERIS_ROOT_DIR, file.filename)
        shutil.copy2(pdf_path, local_pdf)
        
        # Récupération automatique du classpath
        classpath_elements = []
        for root, dirs, files in os.walk(AUDIVERIS_ROOT_DIR):
            for f in files:
                if f.endswith('.jar'):
                    classpath_elements.append(os.path.join(root, f))
        classpath = ":".join(classpath_elements)
        
        # Commande d'exécution pure, sans interférence
        command = f'xvfb-run --auto-servernum java -cp "{classpath}" org.audiveris.Main -batch -transcribe -export=musicxml -output . "{file.filename}"'
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=AUDIVERIS_ROOT_DIR)
        
        # Recherche du fichier MusicXML / MXL généré
        base_name = os.path.splitext(file.filename)[0]
        for root, dirs, files in os.walk(AUDIVERIS_ROOT_DIR):
            for f in files:
                if f.startswith(base_name) and f.lower().endswith(('.mxl', '.musicxml')):
                    return FileResponse(os.path.join(root, f), filename=f)
                    
        return JSONResponse(status_code=500, content={"error": f"Fichier non généré.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)
