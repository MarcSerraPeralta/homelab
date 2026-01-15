#!/bin/bash
LOGFILE="/home/marc/monitoring/data/disk_use.csv"

for i in {1..6}; do
  DISK_USAGE=$(df -k / | awk 'NR==2 {print $3 "," $4}')
  
  printf "used,available\n$DISK_USAGE" > "$LOGFILE"
  
  sleep 10
done
