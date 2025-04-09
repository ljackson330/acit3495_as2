#!/bin/bash
set -e # Exit on error

echo "=== Setting up Docker buildx ==="
# Create a dedicated builder for this task
docker buildx rm builder-amd64 2>/dev/null || true
docker buildx create --name builder-amd64 --driver docker-container --bootstrap
docker buildx use builder-amd64
docker buildx inspect --bootstrap

# Login to ECR
echo "=== Logging into ECR ==="
aws ecr get-login-password --region us-east-2 --profile AdministratorAccess-273354625202 | docker login --username AWS --password-stdin 273354625202.dkr.ecr.us-east-2.amazonaws.com

# Create repositories if they don't exist
echo "=== Creating ECR repositories ==="
aws ecr create-repository --repository-name myapp/analytics --region us-east-2 || true
aws ecr create-repository --repository-name myapp/auth --region us-east-2 || true
aws ecr create-repository --repository-name myapp/backend --region us-east-2 || true
aws ecr create-repository --repository-name myapp/frontend --region us-east-2 || true

# Build and push each image separately
echo "=== Building and pushing analytics image ==="
cd ./analytics_service
docker buildx build --platform=linux/amd64 \
  -t 273354625202.dkr.ecr.us-east-2.amazonaws.com/myapp/analytics:latest \
  --push .
cd ..

echo "=== Building and pushing auth image ==="
cd ./auth_service
docker buildx build --platform=linux/amd64 \
  -t 273354625202.dkr.ecr.us-east-2.amazonaws.com/myapp/auth:latest \
  --push .
cd ..

echo "=== Building and pushing backend image ==="
cd ./backend
docker buildx build --platform=linux/amd64 \
  -t 273354625202.dkr.ecr.us-east-2.amazonaws.com/myapp/backend:latest \
  --push .
cd ..

echo "=== Building and pushing frontend image ==="
cd ./frontend
docker buildx build --platform=linux/amd64 \
  -t 273354625202.dkr.ecr.us-east-2.amazonaws.com/myapp/frontend:latest \
  --push .
cd ..

echo "=== Images built and pushed successfully ==="

# Clean up existing namespace (optional, comment if you want to keep the namespace)
echo "=== Cleaning up previous deployment ==="
kubectl delete namespace myapp || true
echo "Waiting for namespace to be fully deleted..."
sleep 10

# Create namespace
echo "=== Creating namespace ==="
kubectl create namespace myapp

# Apply secrets
echo "=== Applying secrets ==="
kubectl apply -f k8s/secrets.yaml -n myapp

# Apply storage resources
echo "=== Applying storage resources with gp2 storage class ==="
kubectl apply -f k8s/mariadb-pvc.yaml -n myapp
kubectl apply -f k8s/mongodb-pvc.yaml -n myapp

# Apply database deployments
echo "=== Applying database deployments ==="
kubectl apply -f k8s/mariadb-deployment.yaml -n myapp
kubectl apply -f k8s/mariadb-service.yaml -n myapp
kubectl apply -f k8s/mongodb-deployment.yaml -n myapp
kubectl apply -f k8s/mongodb-service.yaml -n myapp

# Wait for databases to be ready
echo "=== Waiting for databases to be ready... ==="
sleep 60

# Apply application services
echo "=== Applying application services ==="
kubectl apply -f k8s/auth-service-deployment.yaml -n myapp
kubectl apply -f k8s/auth-service-service.yaml -n myapp
kubectl apply -f k8s/backend-deployment.yaml -n myapp
kubectl apply -f k8s/backend-service.yaml -n myapp
kubectl apply -f k8s/analytics-service-deployment.yaml -n myapp
kubectl apply -f k8s/analytics-service-service.yaml -n myapp
kubectl apply -f k8s/frontend-deployment.yaml -n myapp
kubectl apply -f k8s/frontend-service.yaml -n myapp

# Apply horizontal pod autoscalers
echo "=== Applying horizontal pod autoscalers ==="
kubectl apply -f k8s/backend-hpa.yaml -n myapp

echo "=== Deployment completed! Checking pod status... ==="
kubectl get pods -n myapp

echo "=== Waiting 30 seconds to check final status ==="
sleep 30
kubectl get pods -n myapp

echo "Press any key to exit..."
read -n 1
