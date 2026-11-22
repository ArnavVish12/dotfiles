#!/usr/bin/env python3
"""EMERGENCY: kill every window on every workspace (SIGTERM to each app).

Use only when the system is lagging badly — apps die immediately
without save prompts.
"""
import json
import os
import signal
import subprocess


def main():
    out = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True,
                         text=True, timeout=10).stdout
    pids = {c["pid"] for c in json.loads(out) if c.get("pid", 0) > 1}
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


if __name__ == "__main__":
    main()
