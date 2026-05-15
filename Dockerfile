FROM eclipse-temurin:17-jdk-focal

# 1. Installation des outils de base
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. TELECHARGEMENT D'AUDIVERIS (Via lien de redirection officiel)
# Cette commande récupère la version 5.3.1 via une URL qui ne dépend pas de la casse
RUN curl -L -o audiveris.zip https://github.com/Audiveris/audiveris/releases/download/v5.3.1/audiveris-5.3.1.zip || \
    curl -L -o audiveris.zip https://github.com/Audiveris/audiveris/releases/download/v5.3.1/Audiveris-5.3.1.zip

RUN unzip audiveris.zip && \
    mv audiveris-* AudiverisApp && \
    rm audiveris.zip

# 3. Copie du projet
COPY . /app/

# 4. Installation Python
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8080

# 5. Lancement
CMD ["python3", "backend/main.py"]
