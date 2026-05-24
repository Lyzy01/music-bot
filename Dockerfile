FROM python:3.10-slim

# Install system dependencies, including FFmpeg for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose the Flask web port for Render
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
