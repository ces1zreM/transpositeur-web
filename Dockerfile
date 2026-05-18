FROM eclipse-temurin:17-jdk-focal

# Installation des outils systèmes nécessaires
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Récupération et extraction d'Audiveris depuis ta Dropbox
RUN mkdir -p /app/audiveris_local
RUN curl -L -o audiveris.zip "https://www.dropbox.com/scl/fi/upb0n3svz386f5tlohi5o/Audiveris.zip?rlkey=3l2sro0c122os3x07pawc822c&st=593l7qze&dl=1"
RUN unzip audiveris.zip -d /app/audiveris_local/ && rm audiveris.zip

# Script d'API Python ultra-léger pour ce serveur dédié
COPY app.py /app/app.py

RUN pip3 install fastapi uvicorn python-multipart

EXPOSE 10000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
