#!/bin/bash -e
date=$(date +%Y%m%d)
log_file="./logs/sticky_note_$date.log"
mkdir -p ./logs
nohup ./app/sticky_note.py -f ./etc/sticky_note.yaml -t diary > "$log_file" 2>&1 &