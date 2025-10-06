FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Create app user for security
RUN useradd --create-home --shell /bin/bash app
# Set work directory
WORKDIR /app
# Clone the repository (replace with your actual repo URL)
# For now, we'll copy the source code, but you can uncomment and modify the git clone line
# RUN git clone https://github.com/your-username/new_temperature.git .
COPY . .
# Change ownership of the app directory to app user
RUN chown -R app:app /app
# Switch to app user
USER app
# Create Python virtual environment
RUN python -m venv /home/app/venv
# Activate virtual environment and upgrade pip
RUN /home/app/venv/bin/pip install --upgrade pip setuptools wheel
# Install Python dependencies
RUN /home/app/venv/bin/pip install -r requirements.txt

# Install gunicorn in the virtual environment (not system-wide)
RUN /home/app/venv/bin/pip install gunicorn
# Create directories for logs and database with proper permissions
RUN mkdir -p /app/logs /app/data
# Create volume mount point for shared database
VOLUME ["/app/data"]
# Set PATH to use virtual environment
ENV PATH="/home/app/venv/bin:$PATH"
# Set Django settings module
ENV DJANGO_SETTINGS_MODULE=temperature.settings
# Expose port (if needed for health checks)
EXPOSE 8000
RUN chmod +x /app/startup.sh
RUN sed -i 's/\r$//' /app/startup.sh
# Set the entrypoint to the startup script
ENTRYPOINT ["bash", "/app/startup.sh", "8000"]