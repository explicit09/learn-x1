#!/bin/bash

# Script to generate Kubernetes secrets for LEARN-X platform

set -e

# Check if .env file exists
if [ ! -f ".env" ]; then
  echo "Error: .env file not found. Please create one with the required environment variables."
  exit 1
fi

# Source environment variables
source .env

# Check required variables
required_vars=("DATABASE_URL" "REDIS_URL" "S3_ACCESS_KEY" "S3_SECRET_KEY" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set in .env file."
    exit 1
  fi
done

# Create secrets.yml from template
cp k8s/secrets-template.yml k8s/secrets.yml

# Replace placeholders with base64 encoded values
sed -i '' "s|BASE64_ENCODED_DATABASE_URL|$(echo -n $DATABASE_URL | base64)|g" k8s/secrets.yml
sed -i '' "s|BASE64_ENCODED_REDIS_URL|$(echo -n $REDIS_URL | base64)|g" k8s/secrets.yml
sed -i '' "s|BASE64_ENCODED_S3_ACCESS_KEY|$(echo -n $S3_ACCESS_KEY | base64)|g" k8s/secrets.yml
sed -i '' "s|BASE64_ENCODED_S3_SECRET_KEY|$(echo -n $S3_SECRET_KEY | base64)|g" k8s/secrets.yml
sed -i '' "s|BASE64_ENCODED_OPENAI_API_KEY|$(echo -n $OPENAI_API_KEY | base64)|g" k8s/secrets.yml

echo "Kubernetes secrets file generated successfully at k8s/secrets.yml"
echo "WARNING: This file contains sensitive information. Do not commit it to version control."
