# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and config
COPY src/ /app/src/
COPY config/ /app/config/

# Copy dataset if necessary (or download it dynamically if not checked in)
COPY data/ /app/data/

# Expose port (Railway will provide the $PORT env var)
EXPOSE 8000

# Start the FastAPI server using Uvicorn
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
