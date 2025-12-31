# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run database migrations and collect static files
RUN python manage.py migrate --noinput || true && \
    python manage.py collectstatic --noinput || true

# Expose port 8000
EXPOSE 8000

# Run Daphne server on 0.0.0.0:8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "cardsnchaos.asgi:application"]
