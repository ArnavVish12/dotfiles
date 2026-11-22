function dotup --description 'Backup ricing dotfiles into ~/dotfiles and commit'
    set -l repo ~/dotfiles
    set -l cfgs hypr waybar fish kitty dunst cava fastfetch zsh bash starship.toml gtk-3.0 gtk-4.0 fontconfig

    for p in $cfgs
        if test -e ~/.config/$p
            rm -rf $repo/config/$p
            cp -a ~/.config/$p $repo/config/$p
        end
    end

    for f in .zshrc .bashrc .bash_profile .bash_logout .profile .vimrc
        test -f ~/$f; and cp -a ~/$f $repo/$f
    end

    cd $repo
    git add -A
    if not git diff --cached --quiet
        git commit -m "update "(date +%Y-%m-%d_%H:%M)
    else
        echo "dotfiles: nothing changed"
    end
    cd - >/dev/null
end
