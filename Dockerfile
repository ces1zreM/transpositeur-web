# 1. Base Java pour Audiveris
FROM openjdk:17-jdk-slim

# 2. Installation de Python, Pip et Tesseract (pour l'OCR d'Audiveris)
RUN apt-get update && apt-get install -y \
    python3 python3-pip tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# 3. Dossier de travail
WORKDIR /app

# 4. Copier les fichiers du backend (qui contient main.py et build)
COPY backend/ /app/backend/

# 5. Installer les bibliothèques Python
RUN pip3 install --no-cache-dir fastapi uvicorn music21 python-multipart

# 6. Télécharger la version JAR d'Audiveris
ADD https://github.com/Audiveris/audiveris/releases/download/v5.3/Audiveris-5.3.jar /app/Audiveris.jar

# 7. Port utilisé par Railway/Render
EXPOSE 8080

# 8. Lancer l'application
CMD ["python3", "backend/main.py"]
