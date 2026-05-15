FROM eclipse-temurin:17-jdk-focal

# 1. Installation des outils système (Tesseract et Ghostscript sont vitaux)
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copie de ton projet GitHub
COPY . /app/

# 3. Installation des bibliothèques Python
RUN pip3 install --no-cache-dir -r requirements.txt

# 4. On place ton JAR au bon endroit pour le main.py
RUN cp backend/audiveris.jar /app/Audiveris.jar

EXPOSE 8080

# 5. Lancement de ton application
CMD ["python3", "backend/main.py"]
