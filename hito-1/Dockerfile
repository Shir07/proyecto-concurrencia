# Usamos una imagen oficial, ligera y estable de Python
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos solo el requirements primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código fuente
COPY . .

# Comando por defecto: ejecuta el benchmark con los valores del repo
CMD ["python", "benchmark.py"]