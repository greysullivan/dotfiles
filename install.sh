#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
apply=false
extras=false
configs_only=false
use_zsh=false

usage() {
    cat <<'HELP'
Grey's Arch desktop

  ./install.sh                         preview
  ./install.sh --apply                 install desktop + restore dotfiles
  ./install.sh --apply --extras --zsh   include extras; make zsh the login shell
  ./install.sh --apply --configs-only  restore files without installing packages

Run as your normal user inside the installed Arch system, after archinstall
and first boot. Requires network access and working sudo. Existing files are
backed up. Package installation uses pacman -Syu --needed with normal prompts.
HELP
}

for arg in "$@"; do
    case "$arg" in
        --apply) apply=true ;;
        --extras) extras=true ;;
        --configs-only) configs_only=true ;;
        --zsh) use_zsh=true ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
done

packages=()
read_packages() {
    local package
    while IFS= read -r package; do
        [[ -z "$package" || "$package" == \#* ]] && continue
        packages+=("$package")
    done < "$1"
}
read_packages "$repo/packages/desktop.txt"
if "$extras"; then read_packages "$repo/packages/extras.txt"; fi

if ! "$apply"; then
    usage
    if ! "$configs_only"; then
        printf '\nPackages (%s):\n%s\n' "${#packages[@]}" "${packages[*]}"
    fi
    printf '\nRestore dotfiles to %s, adapting home paths and backing up existing files.\n' "$HOME"
    if "$use_zsh"; then printf 'Set login shell to /usr/bin/zsh.\n'; fi
    exit 0
fi

if (( EUID == 0 )); then
    printf 'Run this as your normal user, without sudo; package installation uses sudo itself.\n' >&2
    exit 1
fi
if [[ ! -f /etc/arch-release ]]; then
    printf 'This installer requires an installed Arch Linux system.\n' >&2
    exit 1
fi
if ! "$configs_only"; then
    sudo pacman -Syu --needed "${packages[@]}"
fi
command -v python3 >/dev/null || { printf 'Install python first.\n' >&2; exit 1; }
python3 "$repo/manage.py" restore --portable --apply
mkdir -p -- "$HOME/sshot" "$HOME/Drive" "$HOME/.local/state/aerc-setup"
if systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
fi
if "$use_zsh" && [[ "$(getent passwd "$(id -un)" | cut -d: -f7)" != /usr/bin/zsh ]]; then
    chsh -s /usr/bin/zsh
fi
cat <<'DONE'

Ready. From a local TTY, run startx.
Super+Enter opens a terminal; Super+d opens the launcher.

Mail/Spotify/Drive need your account setup. Drive upload and mount units
are available for you to enable after configuring rclone.
Dictation needs a Vosk model under ~/.config/nerd-dictation/model.
For Firefox styling: create a profile first, rerun --configs-only, and set
toolkit.legacyUserProfileCustomizations.stylesheets to true in about:config.
Initialize Firefox before using air-theme on a fresh installation.
DONE
