# ── Etapa 1: Builder (Instalación de dependencias) ──
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Etapa 2: Imagen Final de Producción ──
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/sinergixuser/.local/bin:$PATH

# Crear usuario sin privilegios para seguridad
RUN useradd -m -u 1000 sinergixuser

# Copiar dependencias de producción desde la etapa builder
COPY --from=builder /root/.local /home/sinergixuser/.local

# Copiar código de la aplicación y estáticos
COPY --chown=sinergixuser:sinergixuser . /app

USER sinergixuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
