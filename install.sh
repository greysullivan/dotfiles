#!/usr/bin/env bash
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
apply=false
extras=false
configs_only=false
use_zsh=false
align=false
full=false
install_missing=false
services=false
system=false
profile=source

usage() {
    cat <<'HELP'
Grey's Arch desktop

  ./install.sh --align --profile macbookpro11-4          preview alignment
  ./install.sh --align --profile macbookpro11-4 --apply  align existing configs
  Add --install-missing to install missing dependencies, --services to enable
  ready user services, and --system to apply reviewed administrator settings.
  Add --full to compare/install the entire compatible source package set.

  ./install.sh                         preview
  ./install.sh --apply                 install desktop + restore dotfiles
  ./install.sh --apply --extras --zsh   include extras; make zsh the login shell
  ./install.sh --apply --configs-only  restore files without installing packages

Run as your normal user inside the installed Arch system, after archinstall
and first boot. Requires network access and working sudo. Existing files are
backed up. Package installation uses pacman -Syu --needed with normal prompts.
HELP
}

while (( $# )); do
    arg=$1
    case "$arg" in
        --apply) apply=true ;;
        --extras) extras=true ;;
        --configs-only) configs_only=true ;;
        --zsh) use_zsh=true ;;
        --align) align=true ;;
        --full) full=true ;;
        --install-missing) install_missing=true ;;
        --services) services=true ;;
        --system) system=true ;;
        --profile)
            (( $# >= 2 )) || { printf '%s\n' '--profile needs a value' >&2; exit 2; }
            profile=$2
            shift
            [[ "$profile" == source || "$profile" == macbookpro11-4 ]] || { printf 'Unknown profile: %s\n' "$profile" >&2; exit 2; }
            ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
    shift
done
if "$install_missing" && { ! "$align" || "$configs_only"; }; then
    printf '%s\n' '--install-missing requires --align and cannot accompany --configs-only.' >&2
    exit 2
fi
command -v python3 >/dev/null || { printf 'Install python first.\n' >&2; exit 1; }

packages=()
read_packages() {
    local package
    while IFS= read -r package; do
        [[ -z "$package" || "$package" == \#* ]] && continue
        packages+=("$package")
    done < "$1"
}
if "$full"; then
    read_packages "$repo/packages/full.txt"
else
    read_packages "$repo/packages/desktop.txt"
    if "$extras"; then read_packages "$repo/packages/extras.txt"; fi
fi
if [[ "$profile" == macbookpro11-4 ]]; then packages+=(xorg-xrdb); fi
full_args=()
if "$full"; then full_args+=(--full); fi

if "$align"; then
    python3 "$repo/align.py" audit --profile "$profile" "${full_args[@]}"
fi

if ! "$apply"; then
    usage
    if ! "$configs_only" && ! "$align"; then
        printf '\nPackages (%s):\n%s\n' "${#packages[@]}" "${packages[*]}"
    fi
    printf '\nRestore dotfiles to %s, adapting home paths and backing up existing files.\n' "$HOME"
    if "$use_zsh"; then printf 'Set login shell to /usr/bin/zsh.\n'; fi
    python3 "$repo/manage.py" restore --portable --profile "$profile"
    if "$system"; then
        printf '\nSystem changes will be previewed after home configuration is restored.\n'
    fi
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
python3 "$repo/align.py" check-profile --profile "$profile"
python3 "$repo/manage.py" restore --portable --profile "$profile"
if "$align" && "$install_missing"; then
    missing_output=$(python3 "$repo/align.py" missing --profile "$profile" "${full_args[@]}")
    if [[ -n "$missing_output" ]]; then
        mapfile -t missing <<< "$missing_output"
        sudo pacman -Syu --needed "${missing[@]}"
    fi
elif ! "$configs_only" && ! "$align"; then
    sudo pacman -Syu --needed "${packages[@]}"
fi
python3 "$repo/manage.py" restore --portable --profile "$profile" --apply
mkdir -p -- "$HOME/sshot" "$HOME/Drive" "$HOME/.local/state/aerc-setup"
if systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
fi
if "$services"; then
    python3 "$repo/align.py" services --profile "$profile" --apply
fi
if "$system"; then
    sudo python3 "$repo/align.py" system --profile "$profile" --home "$HOME" --apply
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
For an existing desktop, log out of i3 and run startx again to load all changes.
See ALIGNMENT.md for private prerequisites and the verification checklist.
DONE
