#!/bin/bash

# Helpuvio Deployment Fix Script
# Run this on your server to fix all issues

echo "=========================================="
echo "Helpuvio Deployment Fix Script"
echo "=========================================="

# Step 1: Stop and remove all containers and volumes
echo ""
echo "Step 1: Stopping and removing containers..."
docker-compose down -v

# Step 2: Remove old Docker images to force fresh build
echo ""
echo "Step 2: Removing old Docker images..."
docker rmi helpuvio_backend helpuvio_frontend 2>/dev/null || true

# Step 3: Remove the named volume for node_modules (force fresh install)
echo ""
echo "Step 3: Removing old node_modules volume..."
docker volume rm $(docker volume ls -q | grep frontend_node_modules) 2>/dev/null || true

# Step 4: Rebuild containers from scratch
echo ""
echo "Step 4: Rebuilding containers (no cache)..."
docker-compose build --no-cache

# Step 5: Start containers
echo ""
echo "Step 5: Starting containers..."
docker-compose up -d

# Step 6: Wait for services to start
echo ""
echo "Waiting 15 seconds for services to initialize..."
sleep 15

# Step 7: Show status
echo ""
echo "Container Status:"
docker-compose ps

# Step 8: Show logs
echo ""
echo "=========================================="
echo "Showing logs (Ctrl+C to exit)..."
echo "=========================================="
docker-compose logs -f helpuvio-backend helpuvio-frontend
