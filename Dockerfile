# 1. Start with Python 3.11
FROM python:3.11-slim

# 2. Install FFmpeg and audio libraries (CRITICAL FOR SOUND)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the directory inside the container
WORKDIR /app

# 4. Install your Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your bot code and keep_alive.py
COPY . .

# 6. Run the bot
CMD ["python", "bot.py"]
