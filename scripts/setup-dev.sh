#!/bin/bash

# Script to set up the development environment for LEARN-X platform

set -e

echo "Setting up LEARN-X development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker first."
  exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
  echo "Error: Docker Compose is not installed. Please install Docker Compose first."
  exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Creating .env file from .env.infrastructure template..."
  cp .env.infrastructure .env
  echo "Please update the .env file with your actual values."
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd apps/frontend
npm install
cd ../..

# Install API dependencies
echo "Installing API dependencies..."
cd apps/api
pip install -r requirements.txt
cd ../..

# Create directories for volumes if they don't exist
mkdir -p .docker/postgres_data
mkdir -p .docker/redis_data
mkdir -p .docker/minio_data

# Start the services with Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up -d

# Apply database migrations
echo "Applying database migrations..."
sleep 5 # Wait for the database to be ready
cd apps/api
python -m alembic upgrade head
cd ../..

# Apply vector database migrations
echo "Applying vector database migrations..."
cd apps/api
python scripts/apply_vector_migration.py
cd ../..

echo "Development environment setup complete!"
echo "Frontend: http://localhost:3000"
echo "API: http://localhost:8000"
echo "AI Service: http://localhost:8001"
echo "MinIO Console: http://localhost:9001 (login with minioadmin/minioadmin)"
