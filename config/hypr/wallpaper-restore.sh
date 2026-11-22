#!/bin/bash
# Login wallpaper restore: re-set the chosen wallpaper (permanent until changed).
sleep 1
MODE_FILE="$HOME/.cache/wallpaper-mode.txt"
mode="$(cat "$MODE_FILE" 2>/dev/null)"

if [ -f "$mode" ]; then
  awww img "$mode" --transition-type none
else
  awww restore 2>/dev/null || true
fi
# cava gradient is now a fixed cool-blue (see ~/.config/cava/config).
# wallpaper-to-cava.py sync removed so login no longer overwrites it.
