#!/bin/bash

echo "Starting FFMPEG stream..."
ffmpeg -re -stream_loop -1 -i /root/stream.mp4 -vcodec libx264 -vprofile baseline -g 30 -acodec aac -strict -2 -loop -10 -f flv rtmp://localhost/show/stream -nostdin -nostats </dev/null >/dev/stdout 2>&1 &
echo "Stream started. Play http://<ip-address>:8080/hls/stream.m3u8 "

exec "$@"
