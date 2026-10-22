# Use official Python 3.11 slim base image for lightweight container
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables to optimize Python performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and template UI folder
COPY app.py .
COPY templates/ ./templates/

# Expose port 5000 for network access
EXPOSE 5000

# Create non-root user for security best practices
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Entry point command to start Flask application
CMD ["python", "app.py"]
