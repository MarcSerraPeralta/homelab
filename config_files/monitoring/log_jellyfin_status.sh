#!/bin/bash
LOGFILE="/home/marc/monitoring/data/jellyfin_status.csv"

for i in {1..12}; do
  STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}\n" http://myserver:8096/metrics)

  if [ "$STATUS_CODE" = "200" ]; then
    printf "status\n1" > "$LOGFILE"
  else
    printf "status\n0" > "$LOGFILE"
  fi
  
  sleep 5
done
