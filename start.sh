#!/bin/bash -e
nohup ./app/sticky_note.py -f ./etc/sticky_note.yaml -t diary > /dev/null 2>&1 &