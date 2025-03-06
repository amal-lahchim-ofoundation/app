FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

WORKDIR /app

COPY requirements2.txt /app/requirements2.txt

RUN mkdir -p /root/.cache/pip && \
    pip install --no-cache-dir -r requirements2.txt
    
RUN pip install PyMuPDF

COPY . /app

COPY databaseKey.json /app/databaseKey.json
RUN chmod 600 /app/databaseKey.json

COPY .env /app/.env
RUN chmod 600 /app/.env

ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    FIREBASE_DATABASE_CERTIFICATE=/app/databaseKey.json
    
EXPOSE 5000

CMD ["python3", "app.py"]
