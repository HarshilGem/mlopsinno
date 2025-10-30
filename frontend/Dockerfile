FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY frontend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy app code
COPY frontend/ /app/frontend/

# Copy model artifacts from repo root into image
COPY rf_jamming_model.pkl /app/rf_jamming_model.pkl
COPY scaler.pkl /app/scaler.pkl

EXPOSE 5000

ENV PORT=5000 \
    DB_SERVICE_URL=http://backend:5001

CMD ["python", "/app/frontend/app.py"]


