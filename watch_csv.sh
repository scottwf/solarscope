#!/bin/bash

WATCH_DIR="/home/scott/solar-monitor/data"
IMPORT_SCRIPT="/home/scott/solar-monitor/scripts/import_csv.py"

echo "Watching for new CSV files in $WATCH_DIR..."

inotifywait -m -e close_write --format "%f" "$WATCH_DIR" | while read FILENAME; do
  if [[ "$FILENAME" == *.csv ]]; then
    echo "Detected new CSV: $FILENAME"
    python3 "$IMPORT_SCRIPT"
  fi
done
