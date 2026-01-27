FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Redis client needs some, curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY api_agents/api_gateway/requirements.txt .
# Add commonly used libs that might be missing in gatewayreqs but needed for workers
# (Merging essentially or just ensuring basic ones are there)
RUN pip install --no-cache-dir -r requirements.txt \
    redis \
    celery \
    pymongo \
    requests \
    uvicorn \
    fastapi \
    pydantic \
    python-dotenv

# Copy the entire repository into /app
# Because the docker-compose build context is root (../..),
# this copies api_agents, orchestrator, etc.
COPY . /app

# Set python path to root /app so imports work
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the API Gateway
# Note: updated module path to api_agents.api_gateway.main
CMD ["uvicorn", "api_agents.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
