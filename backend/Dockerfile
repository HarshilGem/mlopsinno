FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Use a simple app-level working directory
WORKDIR /app

# Install system dependencies if needed (uncomment if required)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy backend-specific requirements and install
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

EXPOSE 5001

ENV PORT=5001

# Run the backend server
CMD ["python", "/app/backend/db_app.py"]


