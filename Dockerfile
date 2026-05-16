# Imagen base
FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (cacheo de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Exponer puerto
EXPOSE 8000

# CAMBIO: Sin --reload para producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]