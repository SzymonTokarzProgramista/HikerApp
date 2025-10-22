# ============== Tourismo Backend ==============
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# środowisko (ustaw właściwe wartości w docker run / compose)
ENV DB_USER=root \
    DB_PASS=root \
    DB_HOST=host.docker.internal \
    DB_PORT=3306 \
    DB_NAME=tourismo \
    UPLOAD_DIR=uploads

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
