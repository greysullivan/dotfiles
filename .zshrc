###########################################
#          GREYTHEO ZSH CONFIG            #
###########################################

# =========================================
# A) PERFORMANCE / INSTANT FEEL
# =========================================

# Compinit with caching for fast startup
autoload -Uz compinit
if [[ -n ~/.cache/zsh/zcompdump(#qN.mh+24) ]]; then
    compinit -d ~/.cache/zsh/zcompdump
else
    compinit -C -d ~/.cache/zsh/zcompdump
fi

# Sane zsh options
setopt autocd              # cd by typing directory name
setopt correct             # spell correction for commands
setopt correctall          # spell correction for arguments too
setopt extendedglob        # extended globbing
setopt histignorealldups   # no duplicate entries in history
setopt incappendhistory    # write to history immediately
setopt sharehistory        # share history across sessions
setopt histreduceblanks    # remove extra blanks from history
setopt interactivecomments # allow comments in interactive shell
setopt nocaseglob          # case-insensitive globbing
setopt numericglobsort     # sort numerically when relevant
unsetopt beep              # no beeping

# Completions: readable selection
zmodload zsh/complist
zstyle ':completion:*' menu select
#Selection highlight (white on blue)
zstyle ':completion:*' list-colors 'ma=1;37;44'
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

# Load zsh-completions if available
if [[ -d /usr/share/zsh/site-functions ]]; then
    fpath=(/usr/share/zsh/site-functions $fpath)
fi

# Completion styling
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*' # case insensitive + fuzzy
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' special-dirs true
zstyle ':completion:*:descriptions' format '%F{cyan}-- %d --%f'
zstyle ':completion:*:warnings' format '%F{red}-- no matches --%f'

# =========================================
# D) KEYBINDS
# =========================================

bindkey -e  # emacs mode

# History search on up/down
bindkey '^[[A' history-beginning-search-backward
bindkey '^[[B' history-beginning-search-forward

# Home/End keys
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char

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
alias cleanup='sudo pacman -Rns $(pacman -Qdtq)'

# Quick commands
alias ff='fastfetch'
alias rclone='nocorrect rclone'
alias daw='lmms'
alias cava="$HOME/.local/bin/cava-float"
alias think='/home/grey/Documents/think-site/launch_think_.1.sh'

# Games
alias emerald='retroarch -L "$HOME/.config/retroarch/cores/mgba_libretro.so" "$HOME/Downloads/Pokemon-Emerald.gba"'

# GUI apps (detached from terminal)
alias spotify='nohup spotify &>/dev/null & disown'
music() { "$HOME/.local/bin/music"; }
alias firefox='nohup firefox &>/dev/null & disown'
alias dolphin='nohup dolphin &>/dev/null & disown'
alias kate='nohup kate &>/dev/null & disown'
alias kdeconnect='nohup kdeconnect-app &>/dev/null & disown'
alias thunar='nohup thunar &>/dev/null & disown'
alias simplenote='nohup /opt/Simplenote/simplenote --auto-hide-menu-bar &>/dev/null & disown'

# Wallpaper selection
alias landscape='feh --bg-fill ~/Pictures/i3_wp/wp_landscape.jpg'
alias bus='feh --bg-fill ~/Pictures/i3_wp/wp_back_of_a_bus.jpg'
alias forrest='feh --bg-fill ~/Pictures/i3_wp/wp_forrest.jpg'
alias wood='feh --bg-fill ~/pictures/i3_wp/wp_wood.jpg'
alias anime='feh --bg-fill ~/Pictures/i3_wp/wp_anime.jpg'
alias tagroom='feh --bg-fill ~/Pictures/i3_wp/wp_tagroom.jpg'
alias tagwall='feh --bg-fill ~/Pictures/i3_wp/wp_tagwall.jpg'
alias grafwall='feh --bg-fill ~/Pictures/i3_wp/wp_grafwall.jpg'
alias star='feh --bg-fill ~/Pictures/i3_wp/wp_star.jpg'

# Terminal browser with white-steel theme
alias lynx='lynx -lss=/home/grey/.config/lynx/lynx.lss'

# =========================================
# F) FUNCTIONS
# =========================================

# Create directory and cd into it
mkcd() { mkdir -p "$1" && cd "$1"; }

# Launch any GUI app detached from terminal
launch() { nohup "$@" &>/dev/null & disown; }

# Quick help - tldr or man
help() { tldr "$1" 2>/dev/null || man "$1"; }

# Preview files with bat, or dir contents with eza
peek() {
    if [[ -d "$1" ]]; then
        eza -la --icons=auto --git "$1"
    else
        bat --style=numbers,changes "$1"
    fi
}

# Extract common archives
extract() {
    if [[ -f "$1" ]]; then
        case "$1" in
            *.tar.bz2) tar xjf "$1" ;;
            *.tar.gz)  tar xzf "$1" ;;
            *.tar.xz)  tar xJf "$1" ;;
            *.bz2)     bunzip2 "$1" ;;
            *.gz)      gunzip "$1" ;;
            *.tar)     tar xf "$1" ;;
            *.tbz2)    tar xjf "$1" ;;
            *.tgz)     tar xzf "$1" ;;
            *.zip)     unzip "$1" ;;
            *.Z)       uncompress "$1" ;;
            *.7z)      7z x "$1" ;;
            *.rar)     unrar x "$1" ;;
            *)         echo "Unknown archive format: $1" ;;
        esac
    else
        echo "File not found: $1"
    fi
}

# Process search with nicer output
psgrep() { ps aux | head -1; ps aux | command grep -i "$1" | command grep -v grep; }

# Force 256-color mode for ranger so the lavender colorscheme renders consistently
# across kitty (xterm-kitty) and xfce4-terminal (xterm-256color)
ranger() { TERM=xterm-256color command ranger "$@"; }

# =========================================
# G) ZSH PLUGINS
# =========================================

# Syntax highlighting
[[ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] && \
    source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# Autosuggestions
[[ -f /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]] && \
    source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=20

# History substring search
if [[ -f /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh ]]; then
    source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
    bindkey '^[[A' history-substring-search-up
    bindkey '^[[B' history-substring-search-down
fi

# =========================================
# H) FZF + ZOXIDE
# =========================================

# FZF keybindings and completion
[[ -f /usr/share/fzf/key-bindings.zsh ]] && source /usr/share/fzf/key-bindings.zsh
[[ -f /usr/share/fzf/completion.zsh ]] && source /usr/share/fzf/completion.zsh

# FZF defaults - use fd for speed
export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --exclude .git'

# Zoxide (smart cd)
command -v zoxide &>/dev/null && eval "$(zoxide init zsh)"


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

# Run fastfetch unless SKIP_FASTFETCH is set
[[ -z "$SKIP_FASTFETCH" ]] && command -v fastfetch &>/dev/null && { clear; fastfetch; }

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
export PATH="$HOME/.local/bin:$PATH"
# API keys loaded from ~/.secrets
[[ -f ~/.secrets ]] && source ~/.secrets

# --- Grey CLI capture layer ---

ask() {
  if [ -z "$*" ]; then
    echo "usage: ask <text to copy>"
    return 1
  fi
  echo "$*" | xclip -selection clipboard
  echo "→ copied to clipboard"
}

clip() {
  xclip -selection clipboard
  echo "→ output copied to clipboard"
}
#Clean up cache
alias cleanup='sudo paccache -r && yay -Sc --noconfirm && rm -rf ~/.cache/*'

# --- Kitty environment instances ---
dev() { kitty --detach --start-as=fullscreen --config ~/.config/kitty/dev-session.conf --session ~/.config/kitty/sessions/dev; i3-msg move scratchpad; }

# www — awrit browser: direct in kitty, spawn kitty+awrit and exit if in xfce4-terminal
www() {
  local url="${1:-https://duckduckgo.com}"
  if [[ -n "$KITTY_WINDOW_ID" ]]; then
    awrit "$url" "${@:2}"
  else
    kitty --detach awrit "$url" "${@:2}"
    exit
  fi
}

# thinkyank — compile archive_txt notes into think_archives and clear
alias thinkyank='python3 ~/Documents/think-site/thinkyank.py'

# ncspot — use greybone muted theme inside dev session (KITTY_DEV_SESSION=1)
ncspot() {
  if [[ -n "$KITTY_DEV_SESSION" ]]; then
    XDG_CONFIG_HOME=~/.config/ncspot-dev command ncspot "$@"
  else
    command ncspot "$@"
  fi
}
