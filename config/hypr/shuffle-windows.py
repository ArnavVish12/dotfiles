#!/usr/bin/env python3
"""Shuffle windows on the active workspace.
2 windows  -> swap them.
3+ windows -> series of random swaps (positions get shuffled).
"""
import json
import random
import subprocess

DIRS = ["left", "right", "up", "down"]


def ev(code):
    r = subprocess.run(["hyprctl", "eval", code], capture_output=True,
                       text=True, timeout=10)
    return r.stdout.strip()


def query(*args):
    out = subprocess.run(["hyprctl", *args], capture_output=True,
                         text=True, timeout=10).stdout
    return json.loads(out)


def tiled_on_ws(ws):
    return [c["address"] for c in query("clients", "-j")
            if c.get("workspace", {}).get("id") == ws
            and not c.get("floating", False)]


def main():
    ws = query("activeworkspace", "-j")["id"]
    try:
        active = query("activewindow", "-j")["address"]
    except Exception:
        active = None
    addrs = tiled_on_ws(ws)
    if len(addrs) < 2:
        return
    if len(addrs) == 2:
        ev(f'hl.dispatch(hl.dsp.focus({{window="address:{addrs[0]}"}}))')
        for d in DIRS:
            out = ev(f'hl.dispatch(hl.dsp.window.swap({{direction="{d}"}}))')
            if "ok" in out:
                break
    else:
        for _ in range(len(addrs) * 2):
            a = random.choice(addrs)
            ev(f'hl.dispatch(hl.dsp.focus({{window="address:{a}"}}))')
            ev(f'hl.dispatch(hl.dsp.window.swap({{direction="{random.choice(DIRS)}"}}))')
    if active:
        ev(f'hl.dispatch(hl.dsp.focus({{window="address:{active}"}}))')
    ev(f"hl.dispatch(hl.dsp.focus({{workspace={ws}}}))")


if __name__ == "__main__":
    main()
