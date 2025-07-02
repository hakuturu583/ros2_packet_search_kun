FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install the package
RUN pip install -e .

# Install Prometheus client
RUN pip install prometheus-client

# Expose metrics port
EXPOSE 8000

# Run the DDS monitor
CMD ["python", "-m", "ros2_packet_search_kun.prometheus_exporter"]