FROM python:3.12.16-slim-trixie

# Install networking utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        socat && \
    rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p /app /data

# Set the working directory
WORKDIR /app
