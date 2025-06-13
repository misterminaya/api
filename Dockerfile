FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto, no solo la carpeta app
COPY . .

# Asegura que Python pueda importar la carpeta app como módulo
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
