# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
# 1. Prevents Python from buffering stdout and stderr
# 2. Prevents Python from writing .pyc files
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages.
# For psycopg2, using psycopg2-binary in requirements.txt is often easier
# as it avoids needing to install postgresql-client and build tools.
# RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client

# Install Python dependencies
# Copying requirements.txt first leverages Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Set the working directory to the Django project root inside the container
WORKDIR /app/LibSys

# Run collectstatic to gather all static files for WhiteNoise to serve
RUN python manage.py collectstatic --noinput

# Run the Gunicorn server
# Cloud Run automatically sets the PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "LibSys.wsgi"]