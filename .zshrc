# minimal zshrc
export PATH="$HOME/.local/bin:$PATH"
HISTFILE=~/.zsh_history
HISTSIZE=5000
SAVEHIST=5000
setopt HIST_IGNORE_DUPS SHARE_HISTORY
autoload -Uz compinit && compinit
setopt CORRECT
PROMPT='%n@I_hate_windows %1~ %# '

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias cmatrix='cmatrix -C blue'
alias anid='ani-cli --dub -q 360p'
alias gdmini='python3 ~/games/gd-mini/gd-mini.py'
alias limbo="hyprctl eval 'hl.exec_cmd(\"python3 /home/arnav/.config/hypr/limbo.py\")' >/dev/null 2>&1; exit"

# fastfetch: grey-arch normally, tiny logo only in very narrow terminals
fastfetch() {
  if [ "${COLUMNS:-120}" -lt 70 ]; then
    command fastfetch --logo arch_small "$@"
  else
    command fastfetch "$@"
  fi
}
