FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src

RUN pip install --no-cache-dir -e ".[llm,discord]"
RUN pip install --no-cache-dir google-generativeai

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose the API port for Render
EXPOSE 8000

# Script to run all services
COPY <<EOF /app/start.sh
#!/bin/bash
# 1. Start the API in the background (Port 8000)
python -m agentic_os.api.main --port \$PORT &

# 2. Start the Reminder Daemon in the background
dex daemon --interval 30 &

# 3. Start the Discord Bot (Foreground - keeps container alive)
dex discord
EOF

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]

