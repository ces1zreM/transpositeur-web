FROM eclipse-temurin:17-jdk-focal

RUN apt-get update && apt-get install -y \
    python3 python3-pip tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# On copie tout le projet
COPY . /app/

# On installe les bibliothèques
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# On s'assure que le JAR est au bon endroit pour le main.py
RUN cp backend/audiveris.jar /app/Audiveris.jar

EXPOSE 8080

CMD ["python3", "backend/main.py"]
