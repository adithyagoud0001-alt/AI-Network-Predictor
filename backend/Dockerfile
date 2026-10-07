FROM python:3.12-slim

# Install system dependencies for network probing (ping, ifconfig, iwconfig)
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    net-tools \
    wireless-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specification
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
