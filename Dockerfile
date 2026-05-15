# 1. Utilisation d'une image stable avec Java
FROM eclipse-temurin:17-jdk-focal

# 2. Installation de Python, Pip et Tesseract
RUN apt-get update && apt-get install -y \
    python3 python3-pip tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# 3. Dossier de travail
WORKDIR /app

# 4. Copier les fichiers du backend
COPY backend/ /app/backend/

# 5. Installation des dépendances Python
RUN pip3 install --no-cache-dir fastapi uvicorn music21 python-multipart

# 6. Télécharger Audiveris (Lien corrigé vers la version 5.3)
ADD https://github.com/Audiveris/audiveris/releases/download/v5.3/audiveris-5.3.jar /app/Audiveris.jar

# 7. Port pour Render
EXPOSE 8080

# 8. Lancer l'application
CMD ["python3", "backend/main.py"]
