# ============================================================
# Assistant - Backend FastAPI
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Dependances systeme necessaires (compilation de certains paquets Python,
# extraction PDF/DOCX, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dependances Python d'abord (optimise le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif
COPY . .

# Dossiers de donnees persistantes (montes en volume via docker-compose)
RUN mkdir -p data/chroma_db data/uploads logs

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]