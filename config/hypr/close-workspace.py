#!/usr/bin/env python3
"""Close every window on the currently active workspace."""
import json
import subprocess


def ev(code):
    subprocess.run(["hyprctl", "eval", code],
                   capture_output=True, timeout=10)


def query(*args):
    out = subprocess.run(["hyprctl", *args], capture_output=True,
                         text=True, timeout=10).stdout
    return json.loads(out)


def main():
    ws = query("activeworkspace", "-j")["id"]
    addrs = [c["address"] for c in query("clients", "-j")
             if c.get("workspace", {}).get("id") == ws]
    for addr in addrs:
        ev(f'hl.dispatch(hl.dsp.focus({{window="address:{addr}"}}))')
        ev("hl.dispatch(hl.dsp.window.close())")
    ev(f"hl.dispatch(hl.dsp.focus({{workspace={ws}}}))")


if __name__ == "__main__":
    main()
