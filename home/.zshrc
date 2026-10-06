###########################################
#          GREYTHEO ZSH CONFIG            #
###########################################

# =========================================
# A) PERFORMANCE / INSTANT FEEL
# =========================================

# User commands and completion paths must exist before compinit/plugins.
typeset -U path fpath
path=("$HOME/.local/bin" $path)
[[ -d /usr/share/zsh/site-functions ]] && fpath=(/usr/share/zsh/site-functions $fpath)
export PATH

# Create the cache on first launch; retain compinit's security checks.
autoload -Uz compinit
_zsh_cache=${XDG_CACHE_HOME:-$HOME/.cache}/zsh
if (umask 077; command mkdir -p -- "$_zsh_cache"); then
    compinit -d "$_zsh_cache/zcompdump-$ZSH_VERSION"
else
    compinit -D
fi
unset _zsh_cache

# Sane zsh options
setopt autocd              # cd by typing directory name
setopt correct             # spell correction for commands
unsetopt correctall        # leave filenames and arguments as typed
setopt extendedglob        # extended globbing
setopt histignorealldups   # no duplicate entries in history
unsetopt incappendhistory  # sharehistory already writes and imports entries
setopt sharehistory        # share history across sessions
setopt histreduceblanks    # remove extra blanks from history
setopt interactivecomments # allow comments in interactive shell
setopt nocaseglob          # case-insensitive globbing
setopt numericglobsort     # sort numerically when relevant
unsetopt beep              # no beeping

# SluntShack presentation
[[ -r ~/.config/air-theme/shell-colours.zsh ]] && source ~/.config/air-theme/shell-colours.zsh

# Completions: readable selection
zmodload zsh/complist
# If you use autosuggestions (faint grey) bump it up:
# (this only works if zsh-autosuggestions is installed)
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=250'

# =========================================
# B) HISTORY
# =========================================

HISTFILE=~/.zsh_history
HISTSIZE=100000
SAVEHIST=100000
HISTTIMEFORMAT="[%F %T] "

# =========================================
# C) COMPLETION + COLORS
# =========================================

# Completion styling
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*' # case insensitive + fuzzy
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS} 'ma=0;38;2;0;0;0;48;2;255;61;0'
zstyle ':completion:*' special-dirs true
zstyle ':completion:*:descriptions' format '%F{cyan}-- %d --%f'
zstyle ':completion:*:warnings' format '%F{#A3A3A3}-- no matches --%f'

# =========================================
# D) KEYBINDS
# =========================================

bindkey -e  # emacs mode

# Home/End keys
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char

# Use the terminal's actual sequences (Linux console and tmux differ).
zmodload zsh/terminfo
[[ -n ${terminfo[khome]:-} ]] && bindkey "$terminfo[khome]" beginning-of-line
[[ -n ${terminfo[kend]:-} ]] && bindkey "$terminfo[kend]" end-of-line
[[ -n ${terminfo[kdch1]:-} ]] && bindkey "$terminfo[kdch1]" delete-char

# Ctrl+arrow word navigation
bindkey '^[[1;5C' forward-word
bindkey '^[[1;5D' backward-word

# =========================================
# E) ALIASES
# =========================================

# Navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias c='clear'

# Safer operations
alias cp='cp -iv'
alias mv='mv -iv'
alias rm='rm -Iv'

# Modern tools (conditional)
if command -v eza &>/dev/null; then
    alias ls='eza --group-directories-first --icons=auto'
    alias ll='eza -l --group-directories-first --icons=auto --git'
    alias la='eza -la --group-directories-first --icons=auto --git'
    alias lt='eza -T --icons=auto --level=2'
    alias tree='eza -T --icons=auto'
fi

if command -v bat &>/dev/null; then
    alias cat='bat --paging=never --style=plain'
    alias catn='bat'
fi

# System utilities
alias psg='ps aux | command grep -i'
alias df='df -h'
alias du='du -h'
alias free='free -h'

# Pacman helpers
alias update='sudo pacman -Syu'
alias install='sudo pacman -S'
alias remove='sudo pacman -Rns'
alias search='pacman -Ss'

# Remove orphan packages only when the query succeeds and finds packages.
cleanup() {
    local orphan_output orphan_result
    local -a orphan_packages
    orphan_output=$(command pacman -Qdtq 2>&1)
    orphan_result=$?
    # Pacman returns 1, without output, when there are no matching packages.
    if (( orphan_result != 0 )) && ! [[ $orphan_result == 1 && -z $orphan_output ]]; then
        print -u2 -- "$orphan_output"
        return "$orphan_result"
    fi
    orphan_packages=("${(@f)orphan_output}")
    orphan_packages=("${(@)orphan_packages:#}")
    if (( ${#orphan_packages} == 0 )); then
        print 'No orphan packages.'
        return 0
    fi
    command sudo pacman -Rns -- "${orphan_packages[@]}"
}

# Desktop, wallpaper, and old script aliases are deferred; see REVIEW.md.

# =========================================
# F) FUNCTIONS
# =========================================

# ncspot uses Kitty for full-resolution album artwork.
ncspot() {
    if [[ -z ${KITTY_WINDOW_ID:-} ]]; then
        kitty --detach ncspot "$@"
    else
        command ncspot "$@"
    fi
}

# Create directory and cd into it
mkcd() {
    (( $# == 1 )) || { print -u2 'usage: mkcd <directory>'; return 2; }
    command mkdir -p -- "$1" && builtin cd -- "$1"
}

# Launch a GUI app in a new session so it survives this terminal.
# Routine output is retained in one small state log for troubleshooting.
launch() {
    if (( $# == 0 )); then
        print -u2 'usage: launch <gui-command> [arguments...]'
        return 2
    fi
    if ! (( $+commands[$1] )); then
        print -u2 "launch: command not found: $1"
        return 127
    fi

    local launch_state=${XDG_STATE_HOME:-$HOME/.local/state}
    command mkdir -p -- "$launch_state"
    command setsid -f -- "$@" </dev/null >>"$launch_state/gui-launch.log" 2>&1 || {
        print -u2 "launch: failed to start $1 (see $launch_state/gui-launch.log)"
        return 1
    }
}

# Firefox is a desktop app: detach it so closing the terminal does not stop it.
firefox() { launch firefox "$@"; }
firefox-detached() { firefox "$@"; }
# Open the themed browser through the detached desktop launcher.
alias web='firefox-detached'

# Quick help - tldr or man
help() { tldr "$1" 2>/dev/null || man "$1"; }

# Preview files with bat, or dir contents with eza
peek() {
    (( $# == 1 )) || { print -u2 'usage: peek <path>'; return 2; }
    if [[ -d "$1" ]]; then
        if (( $+commands[eza] )); then
            command eza -la --icons=auto --git -- "$1"
        else
            command ls -la -- "$1"
        fi
    else
        if (( $+commands[bat] )); then
            command bat --style=numbers,changes -- "$1"
        else
            command cat -- "$1"
        fi
    fi
}

# Extract common archives
extract() {
    (( $# == 1 )) || { print -u2 'usage: extract <archive>'; return 2; }
    local archive="$1"
    [[ $archive == -* ]] && archive="./$archive"
    if [[ -f "$1" ]]; then
        case "$archive" in
            *.tar.bz2) tar xjf "$archive" ;;
            *.tar.gz)  tar xzf "$archive" ;;
            *.tar.xz)  tar xJf "$archive" ;;
            *.bz2)     bunzip2 "$archive" ;;
            *.gz)      gunzip "$archive" ;;
            *.tar)     tar xf "$archive" ;;
            *.tbz2)    tar xjf "$archive" ;;
            *.tgz)     tar xzf "$archive" ;;
            *.zip)     unzip "$archive" ;;
            *.Z)       uncompress "$archive" ;;
            *.7z)      7z x "$archive" ;;
            *.rar)     unrar x "$archive" ;;
            *)         print -u2 "Unknown archive format: $1"; return 2 ;;
        esac
    else
        print -u2 "File not found: $1"
        return 1
    fi
}

# Process search with nicer output
psgrep() { ps aux | head -1; ps aux | command grep -i "$1" | command grep -v grep; }

# =========================================
# G) ZSH PLUGINS
# =========================================

# Autosuggestions
[[ -f /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]] && \
    source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# History substring search
if [[ -f /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh ]]; then
    source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
    bindkey '^[[A' history-substring-search-up
    bindkey '^[[B' history-substring-search-down
    [[ -n ${terminfo[kcuu1]:-} ]] && bindkey "$terminfo[kcuu1]" history-substring-search-up
    [[ -n ${terminfo[kcud1]:-} ]] && bindkey "$terminfo[kcud1]" history-substring-search-down
else
    bindkey '^[[A' history-beginning-search-backward
    bindkey '^[[B' history-beginning-search-forward
    [[ -n ${terminfo[kcuu1]:-} ]] && bindkey "$terminfo[kcuu1]" history-beginning-search-backward
    [[ -n ${terminfo[kcud1]:-} ]] && bindkey "$terminfo[kcud1]" history-beginning-search-forward
fi

# =========================================
# H) FZF + ZOXIDE
# =========================================

# Use the installed fzf integration once (bindings + completion).
if (( $+commands[fzf] )); then
    eval "$(fzf --zsh)"
fi

# FZF defaults - use fd for speed
if (( $+commands[fd] )); then
    export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
    export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
    export FZF_ALT_C_COMMAND='fd --type d --hidden --exclude .git'
fi

# Zoxide (smart cd)
command -v zoxide &>/dev/null && eval "$(zoxide init zsh)"

# Let Yazi return its final directory to this shell.
y() {
    local cwd_file cwd yazi_result
    cwd_file=$(mktemp -t yazi-cwd.XXXXXX) || return 1
    command yazi "$@" --cwd-file="$cwd_file"
    yazi_result=$?
    IFS= read -r cwd < "$cwd_file"
    command rm -f -- "$cwd_file"
    (( yazi_result == 0 )) || return "$yazi_result"
    if [[ -n $cwd && $cwd != $PWD ]]; then
        builtin cd -- "$cwd" || return $?
    fi
    return 0
}


# =========================================
# I) PROMPT
# =========================================

# Use starship if available, otherwise simple prompt
if command -v starship &>/dev/null; then
    eval "$(starship init zsh)"
else
    PROMPT='%F{cyan}%~%f %# '
fi

# =========================================
# STARTUP
# =========================================

# Keep the familiar command name when the original Neofetch is not installed.
if (( ! $+commands[neofetch] && $+commands[neowofetch] )); then
    alias neofetch='neowofetch'
fi

# System overview is manual: neofetch here, or Super-Space from i3.

# =========================================
# J) COLORED MAN PAGES
# =========================================

export LESS_TERMCAP_mb=$'\e[1;35m'    # begin blink
export LESS_TERMCAP_md=$'\e[1;36m'    # begin bold
export LESS_TERMCAP_me=$'\e[0m'       # end mode
export LESS_TERMCAP_se=$'\e[0m'       # end standout
export LESS_TERMCAP_so=$'\e[1;44;33m' # begin standout
export LESS_TERMCAP_ue=$'\e[0m'       # end underline
export LESS_TERMCAP_us=$'\e[1;32m'    # begin underline

# =========================================
# NVIM DEFAULT EDITOR      
# =========================================

export EDITOR="nvim"
export VISUAL="nvim"

###########################################
#            END OF CONFIG                #
###########################################
# Load highlighting last, after all ZLE widgets and integrations.
[[ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] && \
    source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
