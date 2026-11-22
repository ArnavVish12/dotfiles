#!/usr/bin/env python3
"""Waybar KEYS pill: hover tooltip lists every keybind in your Hyprland config."""
import html
import json
import pathlib
import re

LUA = pathlib.Path.home() / ".config/hypr/hyprland.lua"
CONF = pathlib.Path.home() / ".config/hypr/hyprland.conf"

CATS = ["WINDOWS", "WORKSPACES", "APPS & SYSTEM"]

KNOWN = {
    "hl.dsp.window.close()": "Close window",
    "hl.dsp.exit()": "Exit Hyprland",
    'hl.dsp.window.float({ action = "toggle" })': "Toggle float",
    "hl.dsp.window.pseudo()": "Pseudo-tile",
    'hl.dsp.layout("togglesplit")': "Toggle split",
    "hl.dsp.window.drag()": "Move window",
    "hl.dsp.window.resize()": "Resize window",
    'hl.dsp.window.fullscreen({ action = "toggle", mode = "fullscreen" })': "Fullscreen",
    'hl.dsp.workspace.toggle_special("magic")': "Toggle scratchpad",
    'hl.dsp.window.move({ workspace = "special:magic" })': "To scratchpad",
    "hl.dsp.window.move({ workspace = 1 })": "From scratchpad",
    'hl.dsp.submap("mouse")': "Mouse mode ON",
    'hl.dsp.submap("reset")': "Mouse mode OFF",
}

SCRIPTS = {
    "term-cascade.sh": "Cascade terms",
    "close-workspace.py": "Close workspace",
    "shuffle-windows.py": "Shuffle windows",
    "emergency-close.py": "Emergency close",
    "screen-record.sh": "Screen record",
}


def extract_args(s):
    """Split top-level commas, respecting quotes and nesting."""
    args, cur, depth, i, in_str = [], "", 0, 0, False
    n = len(s)
    while i < n:
        c = s[i]
        if in_str:
            cur += c
            if c == "\\":
                if i + 1 < n:
                    cur += s[i + 1]
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            cur += c
        elif c in "([{":
            depth += 1
            cur += c
        elif c in ")]}":
            depth -= 1
            cur += c
        elif c == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    if cur.strip():
        args.append(cur.strip())
    return args


def find_calls(text, name):
    """All name(...) calls as {start, end, prefix, args}."""
    out, i = [], 0
    while True:
        i = text.find(name + "(", i)
        if i == -1:
            return out
        line_start = text.rfind("\n", 0, i) + 1
        prefix = text[line_start:i]
        j = i + len(name) + 1
        depth, in_str = 1, False
        while j < len(text):
            c = text[j]
            if in_str:
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append({
            "start": i,
            "end": j + 1,
            "prefix": prefix,
            "args": extract_args(text[i + len(name) + 1:j]),
        })
        i = j + 1


def eval_key(expr, keyval=None):
    """Evaluate `mainMod .. " + Q"` style key expressions."""
    parts = [p.strip() for p in expr.split("..")]
    if "key" in parts and keyval is None:
        return None
    buf = []
    for p in parts:
        if len(p) >= 2 and p.startswith('"') and p.endswith('"'):
            buf.append(p[1:-1])
        elif p == "mainMod":
            buf.append("SUPER")
        elif p == "key":
            buf.append(str(keyval))
        else:
            return None
    return "".join(buf).strip()


def describe(dsp):
    """1-2 word description for a dispatcher call."""
    d = re.sub(r"\s+", " ", dsp.strip())
    if d in KNOWN:
        return KNOWN[d]

    m = re.match(r"^hl\.dsp\.exec_cmd\((.*)\)$", d, re.S)
    if m:
        arg = m.group(1).strip()
        if arg in ("terminal", "fileManager", "menu"):
            return {"terminal": "Open terminal",
                    "fileManager": "File manager",
                    "menu": "App launcher"}[arg]
        q = re.match(r'^"(.*)"$', arg, re.S)
        cmd = q.group(1) if q else arg
        if "grim" in cmd:
            return "Region shot"
        for needle, desc in SCRIPTS.items():
            if needle in cmd:
                return desc
        if "hyprlock" in cmd:
            return "Lock screen"
        if "wlogout" in cmd:
            return "Logout menu"
        if "wofi" in cmd:
            return "App launcher"
        if "set-volume" in cmd:
            return "Volume up" if "%+" in cmd else "Volume down"
        if "AUDIO_SOURCE" in cmd:
            return "Mic mute"
        if "set-mute" in cmd:
            return "Mute audio"
        if "brightnessctl" in cmd:
            return "Brightness up" if "%+" in cmd else "Brightness down"
        if "playerctl" in cmd:
            if "next" in cmd:
                return "Next track"
            if "previous" in cmd:
                return "Prev track"
            return "Play/pause"
        if "ydotool" in cmd:
            return "Left click" if "0xC0" in cmd else "Right click"
        first = cmd.split()[0] if cmd.split() else cmd
        stem = pathlib.PurePath(first).stem.replace("-", " ").title()
        return (stem or "Run command")[:24]

    if "moveCursorBy" in d:
        return "Move cursor"
    if 'workspace = "e-1"' in d:
        return "Prev workspace"
    if 'workspace = "e+1"' in d:
        return "Next workspace"
    if 'direction = "' in d:
        m = re.search(r'(focus|move)\(\{ direction = "(\w+)"', d)
        if m:
            return f"Focus {m.group(2)}" if m.group(1) == "focus" else f"Move {m.group(2)}"
    if 'submap("mouse")' in d:
        return "Mouse mode ON"
    if 'submap("reset")' in d:
        return "Mouse mode OFF"
    if "hl.dsp.window.fullscreen" in d:
        return "Fullscreen"
    return "Action"


def category(dsp, in_sub):
    if in_sub:
        return "MOUSE MODE"
    if re.search(r"XF86|wpctl|brightnessctl|playerctl|ydotool", dsp):
        return "MEDIA & HARDWARE"
    if re.search(r"workspace|toggle_special|e\+1|e-1|mouse_(?:up|down)", dsp):
        return "WORKSPACES"
    if re.search(r"window\.|layout\(|focus\(\{ direction", dsp):
        return "WINDOWS"
    return "APPS & SYSTEM"


def main():
    entries = []

    def add(cat, key, desc):
        if key and desc:
            # display only — real binds in hyprland.lua keep mouse:272/273
            key = (key.replace("mouse:272", "left click")
                      .replace("mouse:273", "right click"))
            entries.append((cat, key, desc))

    text = LUA.read_text()
    submaps = find_calls(text, "hl.define_submap")
    spans = [(c["start"], c["end"]) for c in submaps]

    # Global binds
    for c in find_calls(text, "hl.bind"):
        if c["prefix"].strip().startswith("--"):
            continue
        if any(s <= c["start"] <= e for s, e in spans):
            continue  # submap binds handled below
        if not c["args"]:
            continue
        key_expr, dsp = c["args"][0], (c["args"][1] if len(c["args"]) > 1 else "")
        tokens = [p.strip() for p in key_expr.split("..")]
        if "key" in tokens:  # SUPER+1..0 workspace loop — skipped to keep tooltip compact
            continue
        cat = category(dsp, False)
        if cat == "MEDIA & HARDWARE":
            continue  # media keys excluded entirely (widest rows, cut off in tooltip)
        add(cat, eval_key(key_expr), describe(dsp))

    # Submap (mouse mode) binds — collected only if MOUSE MODE is in CATS
    if "MOUSE MODE" in CATS:
        for c in submaps:
            if len(c["args"]) < 2:
                continue
            for b in find_calls(c["args"][1], "hl.bind"):
                if not b["args"]:
                    continue
                dsp = b["args"][1] if len(b["args"]) > 1 else ""
                add("MOUSE MODE", eval_key(b["args"][0]), describe(dsp))

    # Extra binds from the legacy hyprland.conf
    if CONF.exists():
        for line in CONF.read_text().splitlines():
            line = line.strip()
            if not line.startswith("bind") or line.startswith("--") or "=" not in line:
                continue
            parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
            if len(parts) < 4:
                continue
            mods, key, disp, args = parts[0], parts[1], parts[2], ",".join(parts[3:])
            combo_parts = [m for m in mods.split() if m] + ([key] if key else [])
            if not combo_parts:
                continue
            combo = " + ".join(combo_parts).replace("SUPER_L", "SUPER (tap)")
            desc = describe(f'hl.dsp.exec_cmd("{args}")') if disp == "exec" else disp
            add("APPS & SYSTEM", combo, desc)

    groups = {}
    for cat, key, desc in entries:
        groups.setdefault(cat, []).append((key, desc))

    lines = ["<b>HYPRLAND KEYBINDS</b>"]
    for cat in CATS:
        rows = groups.get(cat)
        if not rows:
            continue
        kw = max(len(k) for k, _ in rows)
        dw = max(len(d) for _, d in rows)
        lines.append("")
        lines.append("<b>" + html.escape(cat) + "</b>")
        # 2 per line: the tooltip clamps at ~76 chars before GTK wraps rows
        # mid-entry (which jumbles the cells), so keep every line under that.
        per_line = 2
        for i in range(0, len(rows), per_line):
            cells = [
                html.escape(k.ljust(kw)) + "  " + html.escape(d.ljust(dw))
                for k, d in rows[i:i + per_line]
            ]
            lines.append(" | ".join(cells).rstrip())

    print(json.dumps({
        "text": "KEYS",
        "tooltip": "<tt><small>" + "\n".join(lines) + "</small></tt>",
    }))


if __name__ == "__main__":
    main()
