FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for some python packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src

# Install only what's necessary to keep the image slim and memory usage low.
# We avoid [llm] extra to skip torch and transformers which are huge.
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir google-generativeai discord.py fastapi uvicorn pydantic-settings

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
# Disable heavy local embedding models on Render's free tier
ENV DISABLE_SEMANTIC_MEMORY=true

# Expose the API port for Render
EXPOSE 8000

# Script to run all services
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting Dex Multi-Service Container..."

# 1. Start the Reminder Daemon in the background
dex daemon --interval 60 &

# 2. Start the Discord Bot in the background
# We run it in background so it doesn't block the API detection
dex discord &

echo "Waiting for background services to stabilize..."
sleep 5

# 3. Start the API in the foreground (this will be the main process)
# Render needs to see this process binding to the port.
echo "📡 Starting API on port \${PORT:-8000}..."
exec uvicorn agentic_os.api.main:app --host 0.0.0.0 --port \${PORT:-8000}
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
