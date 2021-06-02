#!/bin/bash

echo "Pulling docker containers from Docker hub..."
sudo docker pull davideparpi/nginx-hls-cache
sudo docker pull davideparpi/nginx-rtmp-server
sudo docker pull davideparpi/videoflux-test-client

sudo docker image prune