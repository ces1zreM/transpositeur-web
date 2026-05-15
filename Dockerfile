FROM eclipse-temurin:17-jdk-focal

# 1. Installation de TOUTES les dépendances nécessaires à Audiveris et Python
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    libtesseract-dev \
    libttf-autohint-dev \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copie des fichiers
COPY . /app/

# 3. Installation des bibliothèques Python
RUN pip3 install --no-cache-dir -r requirements.txt

# 4. On place le JAR au bon endroit
RUN cp backend/audiveris.jar /app/Audiveris.jar

EXPOSE 8080

# 5. Lancement avec plus de mémoire autorisée pour Java
CMD ["java", "-Xmx400m", "-Djava.awt.headless=true", "-jar", "/app/Audiveris.jar", "-batch", "-transcribe", "-export", "-output", "/app/output_music", "backend/main.py"] 
# Note : On garde la commande CMD de Python si tu utilises uvicorn dans ton main.py
CMD ["python3", "backend/main.py"]
