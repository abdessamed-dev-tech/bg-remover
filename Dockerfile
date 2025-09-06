# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BG_STORAGE_DIR=/app/storage \
    BG_BASE_URL=http://127.0.0.1:8001

WORKDIR /app

# System deps for pillow/avif and onnx runtime used by rembg
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-turbo-progs libjpeg62-turbo-dev zlib1g-dev libpng-dev libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

