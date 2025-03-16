FROM python:3.10

RUN apt-get update && apt-get install -y build-essential ffmpeg gcc && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app"

WORKDIR /app

COPY requirements2.txt /app/requirements2.txt


RUN mkdir -p /root/.cache/pip && \
    pip install --no-cache-dir -r requirements2.txt
    
RUN pip install pymupdf ffmpeg-python fitz

COPY . /app

COPY databaseKey.json /app/databaseKey.json
RUN chmod 600 /app/databaseKey.json

COPY .env /app/.env
RUN chmod 600 /app/.env

ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080 \
    FIREBASE_DATABASE_CERTIFICATE=/app/databaseKey.json
    
EXPOSE 8080

CMD ["python3", "app.py"]

