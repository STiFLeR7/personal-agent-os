# Stage 1: Build the React Dashboard
FROM node:18-slim AS dashboard-builder
WORKDIR /dashboard
COPY dex-cognitive-dashboard/package*.json ./
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

# 1. Start the Reminder Daemon in the background
dex daemon --interval 60 &

# 2. Start the Discord Bot in the background
dex discord &

echo "Waiting for background services to stabilize..."
sleep 5

# 3. Start the API in the foreground (serves both API and Dashboard)
echo "📡 Starting API and Dashboard on port \${PORT:-8000}..."
exec uvicorn agentic_os.api.main:app --host 0.0.0.0 --port \${PORT:-8000}
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
