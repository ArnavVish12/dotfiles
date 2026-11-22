#!/usr/bin/env python3
"""Waybar custom CPU module: text shows load %, hover tooltip shows temp."""
import json
import os

STAT = "/tmp/waybar-cpu-stat"
HWMON = "/sys/class/hwmon/hwmon2/temp1_input"


def read_cpu():
    parts = open("/proc/stat").readline().split()
    vals = list(map(int, parts[1:8]))
    return sum(vals), vals[3] + vals[4]


total, idle = read_cpu()
usage = 0
if os.path.exists(STAT):
    try:
        pt, pi = map(int, open(STAT).read().split())
        dt, di = total - pt, idle - pi
        if dt > 0:
            usage = round(100 * (dt - di) / dt)
    except Exception:
        pass
with open(STAT, "w") as f:
    f.write(f"{total} {idle}")

try:
    temp = int(open(HWMON).read().strip()) // 1000
    tip = f"CPU temp = {temp}\u00b0C"
except Exception:
    tip = "CPU temp unavailable"

cls = "critical" if usage >= 90 else ("warning" if usage >= 70 else "")
print(json.dumps({"text": f"CPU {usage}%", "tooltip": tip, "class": cls}))
