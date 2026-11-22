#!/bin/bash
# Open 10 terminals in a staggered cascade.
# Hyprland's dwindle layout tiles them and the pop-in animation
# fires per window because of the small delay.
COUNT=${1:-8}
for i in $(seq 1 "$COUNT"); do
    kitty &
    sleep 0.12
done
