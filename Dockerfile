FROM eclipse-temurin:17-jdk-focal

# 1. Installation des dépendances système
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. TELECHARGEMENT D'AUDIVERIS (Correction du lien 404)
# On télécharge la version "bundle" qui contient tout le nécessaire
RUN wget https://github.com/Audiveris/audiveris/releases/download/v5.3.1/audiveris-5.3.1.zip && \
    unzip audiveris-5.3.1.zip && \
    mv audiveris-5.3.1 AudiverisApp && \
    rm audiveris-5.3.1.zip

# 3. Copie de ton projet
COPY . /app/

# 4. Installation des bibliothèques Python
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8080

# 5. Lancement via Python
CMD ["python3", "backend/main.py"]
