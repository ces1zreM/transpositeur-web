FROM eclipse-temurin:17-jdk-focal

# 1. Installation des dépendances système (Tesseract, Ghostscript, et outils de téléchargement)
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. TELECHARGEMENT D'AUDIVERIS COMPLET (Version stable pour Linux)
# On télécharge directement le moteur complet pour éviter les fichiers manquants de Windows
RUN wget https://github.com/Audiveris/audiveris/releases/download/v5.3.1/Audiveris-5.3.1.zip && \
    unzip Audiveris-5.3.1.zip && \
    mv Audiveris-5.3.1 AudiverisApp && \
    rm Audiveris-5.3.1.zip

# 3. Copie de ton code Python et React
COPY . /app/

# 4. Installation de music21 et FastAPI
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8080

# 5. Lancement
CMD ["python3", "backend/main.py"]
