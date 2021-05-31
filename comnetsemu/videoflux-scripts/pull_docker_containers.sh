#!/bin/bash

echo "Pulling docker containers from Docker hub..."
docker pull davideparpi/nginx-hls-cache
docker pull davideparpi/nginx-rtmp-server
docker pull davideparpi/videoflux-test-client

docker image prune