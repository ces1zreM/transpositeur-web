FROM eclipse-temurin:17-jdk-focal

RUN apt-get update && apt-get install -y \
    python3 python3-pip tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# On copie tout le contenu de ton GitHub dans le dossier /app du serveur
COPY . /app/

# CORRECTION ICI : Le fichier est à la racine, donc on enlève "backend/"
RUN pip3 install --no-cache-dir -r requirements.txt

# On s'assure que le JAR est au bon endroit
RUN cp backend/audiveris.jar /app/Audiveris.jar

EXPOSE 8080

CMD ["python3", "backend/main.py"]
