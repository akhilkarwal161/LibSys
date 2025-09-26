FROM python:3.13-slim-bookworm

# Update system packages to address vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Set environment variables for non-interactive commands
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn and other production-specific dependencies
RUN pip install gunicorn

# Copy the rest of the application's code into the container
COPY . .

# Set the working directory to the Django project root inside the container
WORKDIR /app/LibSys

# Set production-specific environment variables for the container
# Replace these values with your actual production settings.
# For Cloud Run, you can set these in the console or with the gcloud CLI.
# This Dockerfile includes them as defaults for demonstration.
ENV DJANGO_DEBUG=False
ENV ALLOWED_HOSTS=libsys-xvhbgr5zoq-as.a.run.app
ENV CSRF_TRUSTED_ORIGINS=https://libsys-xvhbgr5zoq-as.a.run.app

# Replace with your production database URL from Cloud SQL
# You should get this value from your GCP environment, not hard-code it.
#ENV DATABASE_URL=

# Run collectstatic to gather all static files for WhiteNoise to serve
RUN python manage.py collectstatic --noinput

# Run the Gunicorn server
# Cloud Run automatically sets the PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "LibSys.wsgi"]