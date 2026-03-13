# Usa una imagen oficial de Python
FROM python:3.13-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para PostgreSQL/MySQL si las necesitas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . /app/

# Ejecutar collectstatic automáticamente
RUN python manage.py collectstatic --noinput

# Exponer el puerto que usará Gunicorn
EXPOSE 8000

# Comando para arrancar la app con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "EcoEfforts_panel.wsgi:application"]