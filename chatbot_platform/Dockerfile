# Use a lightweight Python base image
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy only necessary files
COPY . .

# Collect static files early to avoid runtime delay
RUN python manage.py collectstatic --noinput

# Expose the port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "chatbot_platform.wsgi:application", "--bind", "0.0.0.0:$PORT"]