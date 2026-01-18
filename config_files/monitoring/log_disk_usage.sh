#!/bin/bash
LOGFILE="/home/marc/monitoring/data/disk_use.csv"

for i in {1..6}; do
  DISK_USAGE=$(df -k / | awk 'NR==2 {print $3 "," $4 "," $3 / $4 }')
  DISK_USAGE_SRV=$(df -k /srv/ | awk 'NR==2 {print $3 "," $4, "," $3 / $4 }')

  printf "used,available,used_fraction,used_srv,available_srv,used_fraction_srv\n$DISK_USAGE,$DISK_USAGE_SRV" > "$LOGFILE"

  sleep 10
done
