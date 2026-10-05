# User-local commands for login shells (including non-interactive ones).
typeset -U path
path=("$HOME/.local/bin" $path)
export PATH
