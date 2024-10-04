# Dockerfile
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies for Alpine and Python
RUN apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    bash \
    curl \
    gettext \
    linux-headers \
    postgresql-client

# Set work directory
WORKDIR /app

# Copy project requirements
COPY requirements.txt /app/

# Install project dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project files
COPY . /app/
# RUN mkdir -p /gunicorn
# COPY ./gunicorn/gunicorn-* /gunicorn/

# Collect static files (for production)
RUN python manage.py collectstatic --noinput

# # Expose the port Django runs on
# EXPOSE 8000

# # Run the application using Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_project_name.wsgi:application"]
