#!/usr/bin/env python3
"""limbo orchestrator: `limbo` in a terminal -> close it, open 6, flash, shuffle 8s, guess.

Flow (mirrors GD limbo last part):
  1. 6 kitty windows open, each red ascii square.
  2. one random window flashes green ~1.5s, back to red.
  3. windows shuffle positions for 8 seconds.
  4. user must type `yes` in the one that flashed.
  5. correct -> all close, one window "YOU WIN";
     wrong   -> all close, one window "you lost bro u dumbahh".
"""
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
CELL = HOME / ".config" / "hypr" / "limbo-cell.py"
N = 6
FLASH_HOLD = 2.0
SHUFFLE_SECS = 8.0
INPUT_TIMEOUT = 120.0


def query(*args):
    out = subprocess.run(["hyprctl", *args], capture_output=True,
                         text=True, timeout=10).stdout
    return json.loads(out)


def ev(code):
    r = subprocess.run(["hyprctl", "eval", code],
                       capture_output=True, text=True, timeout=10)
    return (r.stdout or "") + (r.stderr or "")


def ev_ok(code):
    return "error:" not in ev(code).lower()


def game_titles(game_id):
    return [f"limbo-{game_id}-{i}" for i in range(N)]


def find_addrs(game_id):
    want = set(game_titles(game_id))
    try:
        clients = query("clients", "-j")
    except Exception:
        return []
    return [c["address"] for c in clients if c.get("title") in want]


def find_by_title(game_id):
    """title -> address for game windows."""
    want = set(game_titles(game_id))
    try:
        clients = query("clients", "-j")
    except Exception:
        return {}
    return {c["title"]: c["address"] for c in clients if c.get("title") in want}


def grid_slots():
    """3x2 equal slots on the active monitor. Returns [(x, y, w, h)] * 6."""
    try:
        mons = query("monitors", "-j")
        mon = next((m for m in mons if m.get("focused")), mons[0])
        W, H = mon["width"], mon["height"]
    except Exception:
        W, H = 1366, 768
    left, top, gap = 20, 65, 10
    w = (W - left * 2 - gap * 2) // 3
    h = (H - top - 20 - gap) // 2
    return [(left + c * (w + gap), top + r * (h + gap), w, h)
            for r in range(2) for c in range(3)]


def move_win(addr, x, y):
    out = ev(f'hl.dispatch(hl.dsp.window.move({{x={x}, y={y}, relative=false, window="address:{addr}"}}))')
    if "error:" in out.lower():
        out = ev(f'hl.dispatch(hl.dsp.window.move({{x={x}, y={y}, window="address:{addr}"}}))')
    return "error:" not in out.lower()


def arrange_grid(game_id):
    """Float all 6 game windows into equal grid slots.
    Returns slot->addr list, or None if Hyprland refused (tiled fallback)."""
    by_title = find_by_title(game_id)
    if len(by_title) < N:
        log(f"grid: only {len(by_title)}/{N} found")
        return None
    time.sleep(0.6)  # let new windows settle before float/resize
    slots = grid_slots()
    ordered = [by_title[t] for t in game_titles(game_id)]
    for addr in ordered:
        ok = ev_ok(f'hl.dispatch(hl.dsp.window.float({{window="address:{addr}"}}))')
        log(f"grid float {addr} ok={ok}")
        if not ok:
            return None
    time.sleep(0.3)
    for i, addr in enumerate(ordered):
        x, y, w, h = slots[i]
        ok = ev_ok(f'hl.dispatch(hl.dsp.window.resize({{x={w}, y={h}, relative=false, window="address:{addr}"}}))')
        log(f"grid resize {addr} {w}x{h} ok={ok}")
        if not ok:
            return None
        move_win(addr, x, y)
    time.sleep(0.4)
    # verify actual geometry
    try:
        clients = {c["address"]: c for c in query("clients", "-j")}
    except Exception as e:
        log(f"grid verify query failed: {e}")
        return ordered
    good = 0
    for i, addr in enumerate(ordered):
        c = clients.get(addr, {})
        x, y, w, h = slots[i]
        match = (c.get("floating") is True and list(c.get("size", [])) == [w, h])
        log(f"grid verify slot{i} float={c.get('floating')} at={c.get('at')} size={c.get('size')} want={[w, h]} match={match}")
        good += 1 if match else 0
    if good < N:
        log(f"grid verify: only {good}/{N} match")
        return None
    return ordered  # index = slot, value = addr


def close_addrs(addrs):
    for a in addrs:
        ev(f'hl.dispatch(hl.dsp.focus({{window="address:{a}"}}))')
        ev("hl.dispatch(hl.dsp.window.close())")


def log(msg):
    try:
        with open("/tmp/limbo.log", "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except OSError:
        pass


def main():
    log("limbo start")
    game_id = f"{os.getpid()}-{int(time.time()) % 100000}"
    state = Path(f"/tmp/limbo-{game_id}")
    state.mkdir(parents=True, exist_ok=True)
    correct = random.randint(0, N - 1)
    (state / "correct").write_text(str(correct))
    (state / "phase").write_text("show")

    devnull = subprocess.DEVNULL
    procs = []
    for i in range(N):
        procs.append(subprocess.Popen(
            ["kitty", "-T", f"limbo-{game_id}-{i}",
             "python3", str(CELL), game_id, str(i)],
            stdout=devnull, stderr=devnull, stdin=devnull,
            start_new_session=True))
        time.sleep(0.12)

    # wait for all 6 windows
    addrs = []
    for _ in range(100):
        addrs = find_addrs(game_id)
        if len(addrs) >= N:
            break
        time.sleep(0.1)
    if len(addrs) < N:
        log(f"abort: only {len(addrs)}/{N} windows appeared")
        print(f"limbo: only {len(addrs)}/{N} windows appeared, aborting",
              file=sys.stderr)
        (state / "phase").write_text("done")
        time.sleep(1)
        close_addrs(addrs)
        return
    log(f"6 windows up, correct={correct}")

    time.sleep(1.5)  # let all-red sink in
    (state / "phase").write_text("flash")
    log("phase=flash")
    time.sleep(FLASH_HOLD)

    # Equal-size floating grid so every terminal matches (easier to FOCUS).
    slots = grid_slots()
    grid = arrange_grid(game_id)
    if grid:
        log(f"grid ok: slot0={slots[0]}")
    else:
        log("grid refused, tiled fallback")

    # shuffle positions for 8s
    (state / "phase").write_text("shuffle")
    log("phase=shuffle")
    end = time.time() + SHUFFLE_SECS
    start = time.time()
    if grid:
        # same-size windows, only positions change: swap two slots at a time.
        # ramps up after the 5th second.
        while time.time() < end:
            a, b = random.sample(range(N), 2)
            # refresh addrs in case user closed one; skip dead slots
            live = set(find_addrs(game_id))
            if grid[a] not in live or grid[b] not in live:
                break
            ax, ay, _, _ = slots[a]
            bx, by, _, _ = slots[b]
            move_win(grid[a], bx, by)
            move_win(grid[b], ax, ay)
            grid[a], grid[b] = grid[b], grid[a]
            fast = (time.time() - start) >= 5
            time.sleep(0.25 if fast else 0.35)
    else:
        dirs = ["left", "right", "up", "down"]
        while time.time() < end:
            addrs = find_addrs(game_id) or addrs
            if len(addrs) >= 2:
                a = random.choice(addrs)
                ev(f'hl.dispatch(hl.dsp.focus({{window="address:{a}"}}))')
                ev(f'hl.dispatch(hl.dsp.window.swap({{direction="{random.choice(dirs)}"}}))')
            fast = (time.time() - start) >= 5
            time.sleep(0.25 if fast else 0.35)

    (state / "phase").write_text("input")
    log("phase=input, waiting for answer")

    # wait for first `yes`
    answer = None
    t0 = time.time()
    while time.time() - t0 < INPUT_TIMEOUT:
        try:
            answer = (state / "answer").read_text().strip()
            if answer != "":
                break
        except OSError:
            pass
        # if user closed everything, abort
        if not find_addrs(game_id):
            break
        time.sleep(0.2)

    win = False
    if answer is not None and answer != "":
        try:
            win = int(answer) == correct
        except ValueError:
            win = False
    (state / "phase").write_text("done")
    log(f"answer={answer} win={win}")
    time.sleep(0.8)
    # Kill game windows by process handle (exact, no focus races).
    # Fallback: hyprctl focus+close for any stragglers (e.g. single-instance).
    for p in procs:
        try:
            if p.poll() is None:
                p.kill()
        except OSError:
            pass
    time.sleep(0.5)
    leftovers = find_addrs(game_id)
    if leftovers:
        log(f"closing {len(leftovers)} stragglers via hyprctl")
        close_addrs(leftovers)
    time.sleep(0.5)

    # result window: launch via Hyprland (not as our child) so it
    # survives our exit. Popen children die with us; exec_cmd children don't.
    outcome = "win" if win else "lose"
    ev(f'hl.exec_cmd("kitty -T limbo-result python3 {CELL} result {outcome}")')
    log("result launched")
    # cleanup state (result doesn't need it)
    try:
        for p in state.iterdir():
            p.unlink()
        state.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        try:
            with open("/tmp/limbo.log", "a") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
        raise
