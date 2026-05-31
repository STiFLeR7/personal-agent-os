# Stage 1: Build the React Dashboard
FROM node:20 AS dashboard-builder
WORKDIR /dashboard
COPY dex-cognitive-dashboard/package.json ./
# Remove lock file if it was copied (though we copy package.json only)
# but to be safe if COPY includes it.
RUN rm -f package-lock.json
RUN npm install
COPY dex-cognitive-dashboard/ ./
RUN npm run build

# Stage 2: Run the Python API and Discord Bot
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src

# Install python dependencies
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir google-generativeai discord.py fastapi uvicorn pydantic-settings

# Copy the built dashboard from Stage 1
COPY --from=dashboard-builder /dashboard/dist ./dex-cognitive-dashboard/dist

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DISABLE_SEMANTIC_MEMORY=true

EXPOSE 8000

# Script to run all services
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting Dex Multi-Service Container..."

# Function to run the daemon with auto-restart
run_daemon() {
    while true; do
        echo "🤖 Starting Dex Reminder Daemon..."
        dex daemon --interval 60 || echo "Daemon exited with error"
        echo "⚠️ Daemon crashed or stopped. Restarting in 10s..."
        sleep 10
    done
}

# Function to run the bot with auto-restart
run_bot() {
    while true; do
        echo "🤖 Starting Dex Discord Bot..."
        dex discord || echo "Discord Bot exited with error"
        echo "⚠️ Discord Bot crashed or stopped. Restarting in 10s..."
        sleep 10
    done
}

# Start background services
run_daemon &
run_bot &

echo "Waiting for background services to stabilize..."
sleep 5

# Start uvicorn in foreground
echo "📡 Starting API and Dashboard on port \${PORT:-8000}..."
exec uvicorn agentic_os.api.main:app --host 0.0.0.0 --port \${PORT:-8000}
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
