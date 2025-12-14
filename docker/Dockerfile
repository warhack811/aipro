# =============================================================================
# Mami AI - Docker Image
# =============================================================================
# Multi-stage build ile optimize edilmiş imaj.
#
# Build:
#   docker build -t mami-ai:latest .
#
# Run:
#   docker run -p 8000:8000 --env-file .env mami-ai:latest
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Sistem bağımlılıkları (SQLite derleme için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="Mami AI Team"
LABEL version="4.2.0"
LABEL description="Mami AI - Gelişmiş AI Asistan"

# Ortam değişkenleri
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Runtime sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Builder'dan wheel'ları kopyala ve yükle
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Uygulama dosyalarını kopyala
COPY . .

# Data dizinlerini oluştur
RUN mkdir -p data/images data/uploads data/chroma_db logs

# Non-root kullanıcı oluştur (güvenlik)
RUN useradd --create-home --shell /bin/bash mami \
    && chown -R mami:mami /app
USER mami

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Port
EXPOSE 8000

# Başlatma komutu
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

