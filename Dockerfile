# Use the official Python image
FROM python:3.11-slim

# 1. Install system dependencies (FFMPEG IS HERE)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your code
COPY . .

# 5. Start the bot
CMD ["python", "bot.py"]
