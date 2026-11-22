#!/usr/bin/env python3
"""Derive cava gradient from wallpaper colors. Usage: wallpaper-to-cava.py <image>"""
import colorsys
import subprocess
import sys
from pathlib import Path

from PIL import Image

CAVA_CONFIG = Path.home() / ".config" / "cava" / "config"
DARK_REF = (30, 30, 46)  # #1e1e2e, existing gradient start
LIGHT_REF = (238, 246, 255)  # #eef6ff, existing gradient end


def clamp(v):
    return max(0, min(255, int(round(v))))


def to_hex(rgb):
    return '#%02x%02x%02x' % tuple(clamp(c) for c in rgb)


def luminance(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blend(a, b, t):
    return tuple(clamp(x + (y - x) * t) for x, y in zip(a, b))


def darken(rgb, f):
    return tuple(clamp(c * f) for c in rgb)


def hsv_of(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def extract_accents(image_path):
    im = Image.open(image_path).convert("RGB")
    small = im.resize((80, 80), Image.BILINEAR)
    q = small.quantize(colors=12, method=Image.MEDIANCUT)
    palette = q.getpalette()
    counts = q.getcolors(80 * 80) or []
    colors = []
    for count, idx in counts:
        r, g, b = palette[idx * 3: idx * 3 + 3]
        colors.append(((r, g, b), count))
    colors.sort(key=lambda t: -t[1])

    scored = []
    for rgb, count in colors:
        h, s, v = hsv_of(rgb)
        lum = luminance(rgb)
        # ignore near-black background and near-white for accent search
        if v < 0.12 or lum < 18:
            continue
        if max(rgb) > 245 and min(rgb) > 235:  # near-white
            continue
        score = count * (0.25 + s) * (0.35 + v)
        scored.append((score, rgb, s, v, count))
    scored.sort(key=lambda t: -t[0])

    accents = []
    for _, rgb, s, v, _ in scored:
        if s > 0.18 and v > 0.25:
            accents.append(rgb)
        if len(accents) >= 3:
            break
    if len(accents) < 2:
        # fallback: most common mid-tone colors (not black/white)
        for rgb, _ in colors:
            if rgb in accents:
                continue
            lum = luminance(rgb)
            if 30 < lum < 225:
                accents.append(rgb)
            if len(accents) >= 3:
                break
    if not accents:
        # last resort: wallpaper hue is monochrome, use its mid gray
        for rgb, _ in colors:
            accents.append(rgb)
            break
    return accents


def build_gradient(accents):
    primary = accents[0]
    secondary = accents[1] if len(accents) > 1 else blend(primary, (255, 255, 255), 0.25)
    tertiary = accents[2] if len(accents) > 2 else blend(secondary, (255, 255, 255), 0.3)

    # dark base: primary darkened, blended toward dark ref to stay terminal-friendly
    dark = blend(darken(primary, 0.22), DARK_REF, 0.45)
    mid1 = blend(darken(primary, 0.5), DARK_REF, 0.25)
    mid2 = blend(primary, mid1, 0.35)
    # light end: tinted near-white so bars stay readable on dark background
    light_mid = blend(tertiary, (255, 255, 255), 0.45)
    light = blend(primary, LIGHT_REF, 0.82)
    near_white = blend(secondary, LIGHT_REF, 0.88)

    controls = [dark, mid1, mid2, primary, secondary, tertiary, light_mid, light]
    # enforce strictly increasing luminance for smooth monotonic ramp
    for i in range(1, len(controls)):
        if luminance(controls[i]) <= luminance(controls[i - 1]) + 4:
            # lift toward white just enough to keep rising
            need = luminance(controls[i - 1]) + 10 - luminance(controls[i])
            t = min(0.6, max(0.08, need / 200.0))
            controls[i] = blend(controls[i], (255, 255, 255), t)
    # final tip must stay very light
    if luminance(controls[-1]) < 225:
        controls[-1] = blend(controls[-1], LIGHT_REF, 0.5)
    controls.append(near_white)
    # resample to exactly 8 steps evenly along the control path
    import math
    # compute cumulative distances
    dists = [0.0]
    for i in range(1, len(controls)):
        d = math.dist(controls[i - 1], controls[i])
        dists.append(dists[-1] + d)
    total = dists[-1] or 1.0
    out = []
    seg = 0
    for k in range(8):
        target = total * k / 7.0
        while seg < len(dists) - 2 and dists[seg + 1] < target:
            seg += 1
        span = dists[seg + 1] - dists[seg] or 1.0
        t = (target - dists[seg]) / span
        out.append(blend(controls[seg], controls[seg + 1], t))
    # enforce monotonic luminance on final ramp (resampling can reintroduce dips)
    for i in range(1, len(out)):
        for _ in range(6):
            if luminance(out[i]) > luminance(out[i - 1]) + 3:
                break
            out[i] = blend(out[i], (255, 255, 255), 0.22)
    return [to_hex(c) for c in out]


def update_config(hexes, source):
    text = CAVA_CONFIG.read_text()
    lines = text.splitlines()
    out = []
    for line in lines:
        s = line.strip()
        if s.startswith("gradient_color_"):
            try:
                n = int(s.split("_")[-1].split()[0])
                if 1 <= n <= 8:
                    indent = line[: len(line) - len(line.lstrip())]
                    out.append(f"{indent}gradient_color_{n} = '{hexes[n - 1]}'")
                    continue
            except ValueError:
                pass
        out.append(line)
    # refresh header comment to show auto source
    header = f"# auto from wallpaper: {Path(source).name}"
    if out and "auto from wallpaper" in out[0]:
        out[0] = header
    else:
        out.insert(0, header)
    CAVA_CONFIG.write_text("\n".join(out) + "\n")


def main():
    if len(sys.argv) < 2:
        print("usage: wallpaper-to-cava.py <image>", file=sys.stderr)
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.is_file():
        print(f"not found: {src}", file=sys.stderr)
        sys.exit(1)
    accents = extract_accents(src)
    hexes = build_gradient(accents)
    update_config(hexes, src)
    print(f"{src.name} accents={[to_hex(a) for a in accents]} -> {' '.join(hexes)}")
    # live-reload running cava (SIGUSR1 == press r)
    try:
        subprocess.run(["pkill", "-USR1", "cava"], check=False)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
