# arnav's fish config (migrated from zsh)
fish_add_path $HOME/.local/bin

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias cmatrix='cmatrix -C blue'
alias anid='ani-cli --dub -q 360p'
alias gdmini='python3 ~/games/gd-mini/gd-mini.py'
alias limbo="hyprctl eval 'hl.exec_cmd(\"python3 /home/arnav/.config/hypr/limbo.py\")' >/dev/null 2>&1; exit"
# mus — free music (YouTube via mpv+yt-dlp). Replaces ncspot, no Spotify account.
#   mus            -> interactive search (fzf), Enter plays
#   mus some query -> plays top result directly
function mus --description "search & play music (YouTube, free)"
    if test (count $argv) -eq 0
        set -l q (read -P "music search: " -l)
        if test -z "$q"
            return 1
        end
        set -l tpl (printf '%%(title)s\t%%(id)s')
        set -l pick (yt-dlp --no-warnings --flat-playlist --print "$tpl" "ytsearch:20 $q" 2>/dev/null \
            | fzf --delimiter=(printf '\t') --with-nth=1 --nth=1 --no-sort \
                  --prompt='♪ ' --height=60% --reverse \
            | cut -f2)
        if test -z "$pick"
            return 1
        end
        mpv --no-video --ytdl-format=bestaudio "https://www.youtube.com/watch?v=$pick"
    else
        mpv --no-video --ytdl-format=bestaudio "ytdl://ytsearch:"(string join ' ' $argv)
    end
end
alias mus-next='playerctl next'
alias mus-prev='playerctl previous'
alias mus-toggle='playerctl play-pause'

# fastfetch: grey-arch normally, tiny logo only in very narrow terminals
function fastfetch
    set -l cols (tput cols 2>/dev/null; or echo 120)
    if test $cols -lt 70
        command fastfetch --logo arch_small $argv
    else
        command fastfetch $argv
    end
end

function fish_prompt
    # disabled for starship - restore by deleting starship line below
    echo -n (whoami)"@I_hate_windows "(prompt_pwd)" > "
end

starship init fish | source

# ytp <url-or-search> — audio-only YouTube, ~30MB vs 500MB+ browser
function ytp
    if test (count $argv) -eq 0
        echo "usage: ytp <url | search terms>"
        return 1
    end
    if string match -qr '^https?://' -- $argv[1]
        mpv --no-video --ytdl-format=bestaudio $argv
    else
        mpv --no-video --ytdl-format=bestaudio "ytdl://ytsearch:$argv"
    end
end
function nf --description "new/edit a function"
    if test -z "$argv[1]"
        echo "usage: nf NAME"
        return 1
    end
    set -l file ~/.config/fish/functions/$argv[1].fish
    test -f $file; or printf 'function %s\n    \nend\n' $argv[1] > $file
    nano +2 $file
end

# nano magic: `nano ~/.config/<app>` opens that app's main config file
function nano --description "nano: folders resolve to their config file"
    set -l out
    for a in $argv
        if test -d "$a"
            set -l cfg (pickconf "$a")
            if test (count $cfg) -eq 0
                return 1
            end
            set -a out $cfg[1]
        else
            set -a out $a
        end
    end
    command nano $out
end

# rm nf <name> — delete an nf-created function; every other rm = normal rm
function rm --description "rm nf <name> deletes a fish function"
    if test "$argv[1]" = "nf"
        if test -n "$argv[2]"
            if not command rm ~/.config/fish/functions/$argv[2].fish
                return 1
            end
            functions -e $argv[2]
            echo "deleted $argv[2]"
            return
        end
        if test -e nf
            command rm $argv
            return
        end
        echo "usage: rm nf <name>"
        return 1
    end
    command rm $argv
end
