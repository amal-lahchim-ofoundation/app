# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Copy environment variables
COPY .env ./

# Copy service account keys
COPY firebase_key.json ./
COPY pubsub_key.json ./

# Copy requirements and install them
COPY clean_requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r clean_requirements.txt



# Copy the entire project
COPY . .

# Flask default port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
