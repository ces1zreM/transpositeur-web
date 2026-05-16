FROM eclipse-temurin:17-jdk-focal

# 1. Installation des outils Linux nécessaires
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. TÉLÉCHARGEMENT DEPUIS DROPBOX
RUN curl -L -o audiveris.zip "https://www.dropbox.com/scl/fi/upb0n3svz386f5tlohi5o/Audiveris.zip?rlkey=3l2sro0c122os3x07pawc822c&st=593l7qze&dl=1"

# 3. Création du dossier et décompression automatique
RUN mkdir -p /app/backend/audiveris_local && \
    unzip audiveris.zip -d /app/backend/audiveris_local && \
    rm audiveris.zip

# 4. Copie de ton code GitHub (main.py, build)
COPY . /app/

# 5. Installation des librairies Python
RUN pip3 install --no-cache-dir -r backend/requirements.txt

EXPOSE 8080

CMD ["python3", "backend/main.py"]
