FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY test_run.py ./
COPY docs/schemas/ ./docs/schemas/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Batch parse + rules; mount data at /app/data/data-masc (xml + screenshots)
CMD ["python", "test_run.py", "--dataset", "masc"]
