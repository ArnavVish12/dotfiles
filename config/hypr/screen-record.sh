#!/bin/bash
# Toggle region screen recording: Ctrl+Shift+R starts, again stops.
PIDFILE=/tmp/wf-recorder.pid

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill -INT "$(cat "$PIDFILE")"
    rm -f "$PIDFILE"
    notify-send "Recording saved" "$(ls -t ~/Videos/rec-*.mp4 2>/dev/null | head -1)"
    exit 0
fi

GEOM=$(slurp) || exit 1
OUT=~/Videos/rec-$(date +%Y%m%d-%H%M%S).mp4
wf-recorder -g "$GEOM" -f "$OUT" &
echo $! > "$PIDFILE"
notify-send "Recording started" "$OUT"
