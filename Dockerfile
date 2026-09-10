FROM python:3.12-slim

# ffmpeg: o faster-whisper usa pra decodificar ogg/opus/mp3/m4a antes de transcrever
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/

# MODEL_DIR = volume onde o modelo whisper é cacheado (baixado no 1º /transcribe).
ENV MODEL_DIR=/models
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
