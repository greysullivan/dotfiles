# Restore user-local commands, including Codex, without duplicate entries.
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

#
# ~/.bash_profile
#

[[ -f ~/.bashrc ]] && . ~/.bashrc
