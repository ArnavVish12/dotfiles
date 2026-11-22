#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

export PATH="$HOME/.local/bin:$PATH"

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias cmatrix='cmatrix -C blue'
alias anid='ani-cli --dub -q 360p'
alias gdmini='python3 ~/games/gd-mini/gd-mini.py'
alias limbo="hyprctl eval 'hl.exec_cmd(\"python3 /home/arnav/.config/hypr/limbo.py\")' >/dev/null 2>&1; exit"
PS1='[\u@\h \W]\$ '
