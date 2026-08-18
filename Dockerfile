FROM python:3.11-slim

WORKDIR /app

# Install Python deps (cached layer)
RUN pip install --no-cache-dir fastapi==0.111.* 'uvicorn[standard]>=0.30' pydantic>=2.7

# Copy the server code (local_rebuild package) and the built Vue static files
# (local_rebuild/server/static/index.html must exist locally — run npm run build first)
COPY local_rebuild /app/local_rebuild

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=18722

EXPOSE 18722

# Volumes: logs (events + stdout + device-roles.json) for persistence
VOLUME ["/app/local_rebuild/logs"]

CMD ["python3", "-m", "uvicorn", "local_rebuild.server.main:app", \
     "--host", "0.0.0.0", "--port", "18722", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
