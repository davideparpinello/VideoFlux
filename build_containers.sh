#!/bin/bash

# Run this script to build Docker images from scratch

echo "Building Docker containers from scratch..."

docker build -f docker/Dockerfile.HLS-Cache . -t nginx-hls-cache:latest --no-cache  
docker build -f docker/Dockerfile.HLS-Server . -t nginx-rtmp-server:latest --no-cache   
docker build -f docker/Dockerfile.Test-Client . -t videoflux-test-client:latest --no-cache            