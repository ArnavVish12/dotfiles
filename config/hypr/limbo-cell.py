#!/usr/bin/env python3
"""limbo-cell: one game window OR the result window for the limbo game.

Game cell:   limbo-cell.py <game_id> <idx 0-5>
Result:      limbo-cell.py result win|lose
"""
import os
import sys
import time
from pathlib import Path

RED = "\033[91m"
GREEN = "\033[92m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

SQUARE = [
    "██████████████",
    "██████████████",
    "██████████████",
    "██████████████",
    "██████████████",
    "██████████████",
    "██████████████",
]


def clear():
    os.system("clear")


def show_square(color, title, subtitle=""):
    clear()
    print(f"{BOLD}LIMBO — geometry dash memory{RESET}")
    print(f"{DIM}follow the green...{RESET}\n")
    for row in SQUARE:
        print(f"  {color}{row}{RESET}")
    print()
    if title:
        print(f"  {BOLD}{title}{RESET}")
    if subtitle:
        print(f"  {DIM}{subtitle}{RESET}")


def read_phase(state):
    try:
        return (state / "phase").read_text().strip()
    except OSError:
        return ""


def game_cell(game_id, idx):
    state = Path(f"/tmp/limbo-{game_id}")
    try:
        correct = int((state / "correct").read_text().strip())
    except OSError:
        print("limbo: state missing, exiting")
        time.sleep(2)
        return
    answer_file = state / "answer"

    show_square(RED, "WATCH...", "one will flash green. remember it.")
    while read_phase(state) not in ("flash", "shuffle", "input", "done"):
        time.sleep(0.1)
        if not state.exists():
            return

    # FLASH phase: correct cell goes green briefly
    # (orchestrator holds 'flash' for ~2s)
    if idx == correct:
        show_square(GREEN, "REMEMBER THIS ONE!", "this is the one. track it.")
    else:
        # stay red so only one green is visible
        show_square(RED, "WATCH...", "did you see it?")
    time.sleep(1.6)
    if idx == correct:
        show_square(RED, "NOW TRACK IT!", "don't lose it...")

    while read_phase(state) not in ("shuffle", "input", "done"):
        time.sleep(0.1)
    show_square(RED, "SHUFFLING...", "DON'T BLINK. 8 seconds.")
    while read_phase(state) not in ("input", "done"):
        time.sleep(0.1)

    if read_phase(state) == "done":
        return
    show_square(RED, "WHICH ONE FLASHED GREEN?", "type 'yes' in THAT terminal only.")
    while True:
        if answer_file.exists():
            show_square(RED, "LOCKED IN...", "someone already answered.")
            break
        try:
            ans = input(f"  {BOLD}type 'yes' in THE ONE that flashed green > {RESET}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if ans == "yes":
            try:
                fd = os.open(str(answer_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(idx).encode())
                os.close(fd)
            except FileExistsError:
                pass
            show_square(RED, "LOCKED IN...", "judging...")
            break
        else:
            print(f"  {DIM}only 'yes' counts. try again.{RESET}")

    while read_phase(state) != "done":
        if not state.exists():
            break
        time.sleep(0.2)


def result_window(outcome):
    win = outcome == "win"
    clear()
    if win:
        print(f"{GREEN}{BOLD}")
        print("  ██╗   ██╗ ██████╗ ██╗   ██╗    ██╗    ██╗██╗███╗   ██╗")
        print("  ╚██╗ ██╔╝██╔═══██╗██║   ██║    ██║    ██║██║████╗  ██║")
        print("   ╚████╔╝ ██║   ██║██║   ██║    ██║ █╗ ██║██║██╔██╗ ██║")
        print("    ╚██╔╝  ██║   ██║██║   ██║    ██║███╗██║██║██║╚██╗██║")
        print("     ██║   ╚██████╔╝╚██████╔╝    ╚███╔███╔╝██║██║ ╚████║")
        print("     ╚═╝    ╚═════╝  ╚═════╝      ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝")
        print(f"{RESET}")
        print(f"  {GREEN}{BOLD}YOU WIN. limbo cleared, just like GD.{RESET}")
    else:
        print(f"{RED}{BOLD}")
        print("  YOU LOST")
        print(f"{RESET}")
        print(f"  {RED}{BOLD}you lost bro u dumbahh{RESET}")
        print(f"  {DIM}that wasn't the green one. run `limbo` to retry.{RESET}")
    print()
    try:
        input(f"  {DIM}press ENTER to close...{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "result":
        result_window(sys.argv[2])
        return
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <game_id> <idx>  OR  {sys.argv[0]} result win|lose")
        sys.exit(1)
    game_cell(sys.argv[1], int(sys.argv[2]))


if __name__ == "__main__":
    main()
