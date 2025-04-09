#!/bin/bash

# Build Docker images
docker build -t analytics:latest ./analytics_service
docker build -t auth:latest ./auth_service
docker build -t backend:latest ./backend
docker build -t frontend:latest ./frontend

# Create namespace
kubectl create namespace myapp

# Apply secrets
kubectl apply -f k8s/secrets.yaml -n myapp

# Apply storage resources
kubectl apply -f k8s/mariadb-pvc.yaml -n myapp
kubectl apply -f k8s/mongodb-pvc.yaml -n myapp

# Apply database deployments
kubectl apply -f k8s/mariadb-deployment.yaml -n myapp
kubectl apply -f k8s/mariadb-service.yaml -n myapp
kubectl apply -f k8s/mongodb-deployment.yaml -n myapp
kubectl apply -f k8s/mongodb-service.yaml -n myapp

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 30

# Apply application services
kubectl apply -f k8s/auth-service-deployment.yaml -n myapp
kubectl apply -f k8s/auth-service-service.yaml -n myapp
kubectl apply -f k8s/backend-deployment.yaml -n myapp
kubectl apply -f k8s/backend-service.yaml -n myapp
kubectl apply -f k8s/analytics-service-deployment.yaml -n myapp
kubectl apply -f k8s/analytics-service-service.yaml -n myapp
kubectl apply -f k8s/frontend-deployment.yaml -n myapp
kubectl apply -f k8s/frontend-service.yaml -n myapp

# Apply horizontal pod autoscalers
kubectl apply -f k8s/backend-hpa.yaml -n myapp

echo "Deployment completed! Checking pod status..."
kubectl get pods -n myapp

echo "Press any key to exit..."
read -n 1