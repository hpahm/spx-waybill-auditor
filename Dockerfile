# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8765 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies:
# - poppler-utils: provides 'pdftotext' and 'pdftoppm' for lightning-fast text extraction
# - tesseract-ocr & tesseract-ocr-vie: provides OCR fallback for scanned waybills
# - curl: lightweight healthcheck probe (<2MB RAM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY spx_checker.py app.py check_spx.py ./

# Healthcheck using lightweight curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE 8765

CMD ["python", "app.py"]
