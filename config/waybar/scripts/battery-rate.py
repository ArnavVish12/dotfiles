#!/usr/bin/env python3
"""Waybar custom battery: text like before, tooltip rate in %/min."""
import json
import re
import subprocess

out = subprocess.run(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT1"],
                     capture_output=True, text=True, timeout=10).stdout


def field(name):
    m = re.search(rf"^\s*{name}:\s*(.+)$", out, re.M)
    return m.group(1).strip() if m else ""


state = field("state").lower()
pct = float(field("percentage").rstrip("%") or 0)
rate_w = float(field("energy-rate").split()[0] or 0)
full_wh = float(field("energy-full").split()[0] or 0)
pct_min = (rate_w / full_wh * 100 / 60) if full_wh else 0

if state in ("charging", "pending-charge"):
    t = field("time to full") or field("time to empty")
    icon, cls = "\u26a1", "charging"
elif state == "fully-charged":
    t, icon, cls = "", "\U0001f50c", ""
else:  # discharging (checked last: the word contains "charging")
    t = field("time to empty")
    icon, cls = "", ""
    if pct <= 15:
        cls = "critical"
    elif pct <= 30:
        cls = "warning"

text = f"{icon} {pct:.0f}%" if icon else f" Battery = {pct:.0f}%"
tip = f"Battery: {pct:.0f}%"
if t:
    tip += f"\n{t}"
tip += f"\nRate = {pct_min:.2f}%/min"
print(json.dumps({"text": text, "tooltip": tip, "class": cls}))
