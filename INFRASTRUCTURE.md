# LEARN-X Platform Infrastructure

This document provides information about the infrastructure setup for the LEARN-X platform, including local development with Docker Compose and production deployment with Kubernetes.

## Local Development

### Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ for frontend development
- Python 3.11+ for backend development

### Environment Setup

1. Copy the environment template to create your local environment file:

```bash
cp .env.infrastructure .env
```

2. Update the `.env` file with your actual values, especially the API keys.

### Starting the Development Environment

To start all services locally:

```bash
docker-compose up
```

To start specific services:

```bash
docker-compose up frontend api
```

### Accessing Services

- Frontend: http://localhost:3000
- API: http://localhost:8000
- AI Service: http://localhost:8001
- MinIO Console: http://localhost:9001 (login with minioadmin/minioadmin)

## Production Deployment

### Kubernetes Setup

The LEARN-X platform is designed to be deployed on Kubernetes. The configuration files are located in the `k8s/` directory.

### Prerequisites

- Kubernetes cluster (e.g., EKS, GKE, AKS)
- kubectl configured to access your cluster
- Docker registry for storing container images

### Generating Kubernetes Secrets

1. Ensure your `.env` file contains all required variables
2. Run the secrets generation script:

```bash
./scripts/generate-k8s-secrets.sh
```

3. Apply the generated secrets to your Kubernetes cluster:

```bash
kubectl apply -f k8s/secrets.yml
```

### Deploying to Kubernetes

1. Apply the ConfigMap:

```bash
kubectl apply -f k8s/config.yml
```

2. Deploy all services:

```bash
kubectl apply -f k8s/
```

3. Verify the deployments:

```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

## CI/CD Pipeline

The LEARN-X platform includes a GitHub Actions workflow for continuous integration and deployment. The workflow is defined in `.github/workflows/deploy.yml`.

### CI/CD Process

1. On push to the main branch, the CI/CD pipeline runs tests for all components
2. If tests pass, Docker images are built and pushed to the registry
3. The images are deployed to the Kubernetes cluster

### Required Secrets

The following secrets must be configured in your GitHub repository:

- `DOCKERHUB_USERNAME`: Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `AWS_ACCESS_KEY_ID`: AWS access key for EKS access
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for EKS access

## Infrastructure Components

### Frontend

- Next.js application
- Served via Nginx
- Configured for server-side rendering

### API Service

- FastAPI application
- Handles authentication, course management, and other core features
- Connects to PostgreSQL and Redis

### AI Service

- FastAPI application
- Handles AI tutoring and content generation
- Integrates with OpenAI API

### Worker

- Celery worker
- Processes background tasks
- Connects to Redis for message broker

### Database

- PostgreSQL with pgvector extension
- Stores all application data
- Supports vector embeddings for AI features

### Redis

- Used for caching and as a message broker
- Supports real-time features

### Storage

- S3-compatible storage (MinIO for development, AWS S3 for production)
- Stores user uploads and generated content

## Monitoring and Logging

### Monitoring

The infrastructure includes monitoring via Prometheus and Grafana (to be configured separately).

### Logging

All services log to stdout/stderr, which can be collected by a logging solution like ELK Stack or Datadog.

## Scaling Considerations

- The API and AI services can be scaled horizontally by increasing the number of replicas
- The worker service can be scaled based on queue size
- Database scaling should be handled through a managed service like AWS RDS or Neon PostgreSQL

## Security Considerations

- All services communicate over TLS
- Secrets are managed via Kubernetes Secrets
- API authentication is required for all endpoints
- Row-Level Security (RLS) is implemented in PostgreSQL for multi-tenant isolation

## Backup and Recovery

- Database backups should be configured based on your database provider
- S3 bucket versioning should be enabled for content recovery
- Regular testing of restore procedures is recommended

## Troubleshooting

### Common Issues

1. **Services not starting**: Check Docker logs with `docker-compose logs <service-name>`
2. **Database connection issues**: Verify DATABASE_URL in the .env file
3. **API errors**: Check API logs with `kubectl logs deployment/api-deployment`

### Getting Help

For additional assistance, please contact the development team or refer to the project documentation.
