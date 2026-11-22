#!/usr/bin/env bash
# Roast the user on failed hyprlock logins.
# Escalates with the pam_faillock tally (resets on a correct login, deny=0 so
# no real account lockout). Prints nothing until the first wrong password.
set -u

user="${USER:-$(id -un)}"
file="$HOME/.config/hypr/roasts.txt"

# Count FAILED HYPRLOCK attempts only. faillock keeps ONE per-user tally shared
# across sudo/su/login/hyprlock, so we must filter by source (column 4) — a
# fumbled sudo password must NOT earn you a login-screen roast.
# Row format: <date> <time> <Type=SVC> <Source> <Valid>   (2 header lines first).
count="$(/usr/bin/faillock --user "$user" 2>/dev/null \
  | awk '$1 ~ /^[0-9]{4}-/ && $4 == "hyprlock" {c++} END{print c+0}')"
[ -z "$count" ] && count=0

# No failures yet -> print nothing (label stays empty).
[ "$count" -le 0 ] && exit 0

total="$(grep -c . "$file" 2>/dev/null)"
[ -z "$total" ] || [ "$total" -eq 0 ] && exit 0

# Clamp: past the end of the list, keep repeating the final roast.
[ "$count" -gt "$total" ] && count="$total"

sed -n "${count}p" "$file"
