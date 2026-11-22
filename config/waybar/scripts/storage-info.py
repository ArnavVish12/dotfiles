#!/usr/bin/env python3
"""Waybar storage: pill shows rounded GB, tooltip shows precise values."""
import json
import subprocess

out = subprocess.run(["df", "-B1", "/"], capture_output=True,
                     text=True, timeout=10).stdout.splitlines()[1].split()
total_gb, used_gb = int(out[1]) / 1e9, int(out[2]) / 1e9
free_gb = int(out[3]) / 1e9
print(json.dumps({
    "text": f"{used_gb:.0f}GB/{total_gb:.0f}GB",
    "tooltip": f"Used storage = {used_gb:.2f}GB\nTotal storage = {total_gb:.2f}GB\nStorage left = {free_gb:.2f}GB",
}))
