# Use an official Python runtime as a parent image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y build-essential gcc

# Set environment variables to prevent Python from writing bytecode and using a buffer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first (to leverage Docker caching)
COPY requirements2.txt /app/requirements2.txt

# Enable BuildKit cache for pip (if supported)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements2.txt

# Copy the rest of the application files
COPY . /app

# Ensure the Firebase credentials file is copied with correct permissions
COPY databaseKey.json /app/databaseKey.json
RUN chmod 600 /app/databaseKey.json

# Copy the .env file into the container with correct permissions
COPY .env /app/.env
RUN chmod 600 /app/.env

# Set the environment variable to tell Flask to run the app
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Set the environment variable for Firebase credentials
ENV FIREBASE_DATABASE_CERTIFICATE=/app/databaseKey.json

# Expose the port the app will run on
EXPOSE 5000

# Run the application when the container starts
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

