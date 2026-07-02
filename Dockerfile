# ============================================================
# Stage 1: Builder — instala dependencias con pip
# ============================================================
FROM python:3.12.10-slim-bookworm AS builder

WORKDIR /build

# Instalar sólo lo necesario para compilar paquetes nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --prefix=/install permite copiar sólo los paquetes al stage runtime
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 2: Runtime — imagen final mínima y segura
# ============================================================
FROM python:3.12.10-slim-bookworm AS runtime

# Instalar libpq en runtime (psycopg2-binary la necesita en runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes instalados desde el builder
COPY --from=builder /install /usr/local

# Crear usuario no-root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/sh --create-home appuser

WORKDIR /app

# Copiar SÓLO el código fuente (no .env, no docs, no git)
COPY app/ ./app/
COPY static/ ./static/

# Cambiar propiedad al usuario de la app
RUN chown -R appuser:appgroup /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto de la aplicación
EXPOSE 8000

# Healthcheck interno del contenedor
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Forma exec para manejo correcto de señales SIGTERM
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
