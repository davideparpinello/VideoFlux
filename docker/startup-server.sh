#!/bin/bash

echo "Starting FFMPEG stream..."
ffmpeg -re -stream_loop -1 -i /root/stream.mp4 -vf drawtext="fontfile=monofonto.ttf: fontsize=96: box=1: boxcolor=black@0.75: boxborderw=5: fontcolor=white: x=(w-text_w)/2: y=((h-text_h)/2)+((h-text_h)/4): text='%{gmtime\:%H\\\\\:%M\\\\\:%S}'" -vcodec libx264 -vprofile baseline -g 30 -acodec aac -strict -2 -loop -10 -f flv rtmp://localhost/show/stream -nostdin -nostats </dev/null >/dev/stdout 2>&1 &

echo "Stream started. Play http://<ip-address>:8080/hls/stream.m3u8 "

exec "$@"
