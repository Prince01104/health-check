# Health Check for Google Cloud Run (FastAPI app + models + Gemini chat).
# Build and deploy steps are in README.md ("Deploy on Google Cloud Run").
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    HC_DATA_DIR=/tmp/hc_data

# libglib is needed by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY models ./models

RUN useradd --create-home appuser && mkdir -p /tmp/hc_data && chown -R appuser /tmp/hc_data
USER appuser

# Cloud Run sets $PORT (8080). GEMINI_API_KEY comes from a Cloud Run secret, never from the image.
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
