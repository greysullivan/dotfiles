#!/usr/bin/env bash
# Grey's MacBookAir7,2 bootstrap, 2026-09-19. Run with bash, never source.
# DESTRUCTIVE only with --install and two interactive confirmations.
# No unattended mode. No credentials in this file. No desktop installation.
set -Eeuo pipefail
umask 022

usage() {
  cat <<'HELP'
GREY AIR: Arch Linux bootstrap for MacBookAir7,2 (2015/2017 Air)

  bash grey-air-install.sh --help       Read this guide; no changes
  bash grey-air-install.sh --check      Read-only environment/disk report
  bash grey-air-install.sh --install    Interactive FULL INTERNAL DISK ERASE

BEFORE STARTING
1. Back up all files from the intended laptop. Confirm you can open backups.
2. On the iMac, download a current ISO from https://archlinux.org/download/
   and follow its signature-verification guidance. Write it to a USB using
   a trusted image-writing tool. Writing the ISO erases THAT USB.
3. Put this script on a SECOND USB, not the internal SSD to be erased.
   Disconnect backup disks before installing. Keep the charger connected.
4. Hold Option while starting the Air; select the Arch USB's EFI Boot.
   You need a usable screen/keyboard. No macOS/dual-boot preservation here.
5. Get temporary internet BEFORE installing. Prefer a supported USB Ethernet
   adapter. Phone USB tethering may work; iPhone pairing can require extra
   setup, so do not assume it will work offline. Built-in Broadcom Wi-Fi
   often needs a driver that is not available in the live ISO.
   Check: ip link; networkctl status; curl -I https://archlinux.org
   For Wi-Fi already supported by the live ISO: iwctl (interactive).
6. Find the second USB partition with lsblk -f. Mount THAT partition:
     mkdir -p /run/grey-usb
     mount /dev/REPLACE_WITH_SECOND_USB_PARTITION /run/grey-usb
     cp /run/grey-usb/grey-air-install.sh /root/grey-air-install.sh
     umount /run/grey-usb
   Remove the second USB. Run from RAM:
     bash /root/grey-air-install.sh --check
     bash /root/grey-air-install.sh --install

WHAT IT DOES
Requires official Arch live media, UEFI, x86_64 and MacBookAir7,2.
Requires you to type the whole INTERNAL disk path, then its erase phrase.
Rejects USB/removable disks, mounted disks, active swap and mapped children.
GPT: 1 GiB unencrypted EFI (/boot), remaining disk LUKS2 + ext4 root.
Installs normal and LTS kernels + headers, Broadcom wl DKMS, NetworkManager,
sudo, Git, curl, nano, Neovim, build tools, Node/npm. Visible systemd-boot.
User grey, host air, Pacific/Auckland, en_NZ.UTF-8, US keyboard by default.
Keyboard layout is prompted and used both now and in the encrypted boot.
No graphical login, X11, i3, zsh change, AUR helper or desktop tweaks yet.
Lid-close suspend is disabled initially; test resume before enabling it.
No hibernation or disk swap; RAM management is a later assisted task.
Passwords are prompted directly by cryptsetup/passwd and never logged.
Root password is locked; grey has password-protected sudo access.
LUKS protects data at rest, not the unencrypted boot files from tampering.
TRIM through encryption is not enabled (can disclose allocation patterns).

AFTER SUCCESS
Script unmounts the install and closes LUKS; it does NOT reboot itself.
Type reboot, remove the Arch USB during restart, select EFI Boot if needed.
Unlock LUKS, then log in as grey with the separate account password.
Run nmtui to connect Wi-Fi (select Activate a connection).
Keep the Ethernet/tether fallback until Wi-Fi works across a reboot.
Run: bash ~/install-codex.sh
Then: ~/.local/bin/codex login --device-auth
Complete the displayed login on your iPad/iMac browser. Device-code login
may need enabling in ChatGPT security settings. Never share the code.
Then: cd ~/setup && ~/.local/bin/codex
Ask Codex to read HANDOFF.md before making changes. It will not automatically
have this chat's history. Use its normal approval/sandbox settings.

IF SOMETHING FAILS
Stop. Photograph the error. Do NOT rerun --install: that erases again.
There is no automatic rollback or resume. The filesystem may be mounted
at /mnt and LUKS may still be open as /dev/mapper/cryptroot. Leave them
alone for diagnosis. Before powering down, if those are the installer mounts:
  sync
  umount -R /mnt
  cryptsetup close cryptroot
Do not reboot into an incomplete installation expecting it to work.
If boot fails after success: use the Arch USB, unlock and mount root + EFI,
then arch-chroot /mnt for repair. The earlier PDF has recovery examples;
use your ACTUAL disk names, never assume /dev/sda.

SOURCES (recheck when using an old copy of this script)
https://wiki.archlinux.org/title/Installation_guide
https://man.archlinux.org/man/mkinitcpio.8.en
https://man.archlinux.org/man/systemd-cryptsetup-generator.8.en
https://man.archlinux.org/man/bootctl.1.en
https://archlinux.org/packages/extra/x86_64/broadcom-wl-dkms/
https://developers.openai.com/codex/cli/
https://developers.openai.com/codex/auth/
Original shell: https://github.com/greysullivan/dotfiles/blob/master/.zshrc

VALIDATION LIMIT: static checks only, not tested on physical Mac hardware.
HELP
}
die() { printf '\nSTOP: %s\n' "$*" >&2; exit 1; }
report() {
  printf '\nHardware: '
  cat /sys/class/dmi/id/product_name 2>/dev/null || true
  printf '\nDisks (nothing selected automatically):\n'
  lsblk -e 7 -o NAME,PATH,SIZE,TYPE,TRAN,RM,MODEL,SERIAL,MOUNTPOINTS
  printf '\nNetwork:\n'
  ip -br link
}
mode=${1:---help}
[[ $# -le 1 ]] || die 'Use exactly one option.'
case "$mode" in
  --help|-h) usage; exit 0 ;;
  --check) report; exit 0 ;;
  --install) ;;
  *) die 'Unknown option. Use --help, --check or --install.' ;;
esac
[[ $EUID -eq 0 ]] || die 'Run as root in the official Arch live ISO.'
[[ -t 0 && -t 1 ]] || die 'Interactive terminal required. Do not pipe into bash.'
[[ -d /run/archiso && -f /etc/arch-release ]] || die 'Official Arch live ISO required.'
[[ $(uname -m) == x86_64 && -d /sys/firmware/efi/efivars ]] || die 'Boot x86_64 Arch in UEFI mode.'
[[ $(</sys/class/dmi/id/product_name) == MacBookAir7,2 ]] || die 'This script targets MacBookAir7,2 only.'
for cmd in lsblk cryptsetup sgdisk wipefs partprobe udevadm pacstrap arch-chroot \
  genfstab curl findmnt swapon loadkeys timedatectl mkfs.fat mkfs.ext4; do
  command -v "$cmd" >/dev/null || die "Required live-media command missing: $cmd"
done
[[ ! -e /dev/mapper/cryptroot ]] || die 'cryptroot already exists; diagnose previous install first.'
[[ -z $(findmnt -rn -o TARGET | awk '$0=="/mnt" || index($0,"/mnt/")==1') ]] || die '/mnt has mounted filesystems.'
[[ ! -d /mnt || -z $(find /mnt -mindepth 1 -maxdepth 1 -print -quit) ]] || die '/mnt is not empty.'
[[ -z $(swapon --noheadings --show=NAME) ]] || die 'Active swap detected. Stop and inspect before installing.'
report
printf '\nBackups checked, charger connected, and backup disks disconnected?\n'
read -r -p 'Type BACKED UP to continue: ' answer
[[ $answer == 'BACKED UP' ]] || die 'No backup confirmation.'
read -r -p 'Whole INTERNAL SSD path (example /dev/sda, no default): ' disk_input
[[ $disk_input =~ ^/dev/(sd[a-z]+|nvme[0-9]+n[0-9]+)$ ]] || die 'Unsupported disk path; use the listed whole internal SSD.'
disk=$(readlink -f -- "$disk_input")
[[ -b $disk && $(lsblk -dn -o TYPE "$disk") == disk ]] || die 'Not a whole disk.'
[[ $(lsblk -dn -o RM "$disk") == 0 && $(lsblk -dn -o RO "$disk") == 0 ]] || die 'Disk is removable or read-only.'
transport=$(lsblk -dn -o TRAN "$disk" | tr -d ' ')
[[ $transport == sata || $transport == nvme || $transport == ata ]] || die 'Not a recognized internal SATA/NVMe SSD. Do not bypass without review.'
check_disk_idle() {
  [[ -z $(lsblk -nr -o MOUNTPOINTS "$disk" | tr -d '[:space:]') ]] || die 'Target or child partition is mounted (possibly installer media).'
  while read -r kind; do
    [[ $kind == disk || $kind == part ]] || die 'Target has an active mapper/LVM/RAID child.'
  done < <(lsblk -nr -o TYPE "$disk")
  [[ -z $(swapon --noheadings --show=NAME) ]] || die 'Active swap detected.'
}
check_disk_idle
[[ $(lsblk -bdn -o SIZE "$disk") -ge 32000000000 ]] || die 'Disk smaller than 32 GB.'
read -r -p 'Console keyboard layout [us]: ' keymap
keymap=${keymap:-us}
[[ $keymap =~ ^[A-Za-z0-9_-]+$ ]] || die 'Invalid keyboard layout name.'
loadkeys "$keymap" || die 'Keyboard layout not available.'
printf '\nKeyboard layout loaded. Test a few NON-SECRET characters now.\n'
read -r -p 'Test text (not a password): ' answer
printf 'You typed: %s\n' "$answer"
read -r -p 'Correct keyboard? Type YES: ' answer
[[ $answer == YES ]] || die 'Keyboard not confirmed.'
timedatectl set-ntp true
curl --fail --location --max-time 30 --silent --show-error https://archlinux.org/ >/dev/null || die 'No HTTPS access. Fix temporary internet first.'
packages=(base base-devel linux linux-headers linux-lts linux-lts-headers
  linux-firmware intel-ucode mkinitcpio cryptsetup dosfstools e2fsprogs
  networkmanager broadcom-wl-dkms dkms sudo nano neovim git curl
  man-db man-pages nodejs npm pciutils usbutils)
printf '\nChecking repository packages before erasing. No target changes yet.\n'
pacman -Sy --noconfirm
for package in "${packages[@]}"; do
  pacman -Si "$package" >/dev/null || die "Package unavailable: $package"
done
lsblk -o PATH,SIZE,MODEL,SERIAL,FSTYPE,MOUNTPOINTS "$disk"
printf '\nALL partitions and files on %s WILL BE DESTROYED. No macOS retained.\n' "$disk"
printf 'New layout: 1 GiB EFI + LUKS2 encrypted ext4, account grey, host air.\n'
read -r -p "Type exactly ERASE $disk : " answer
[[ $answer == "ERASE $disk" ]] || die 'Erase confirmation did not match.'
check_disk_idle
stage='partitioning'
trap 'rc=$?; printf "\nFAILED during %s (line %s, code %s). Do not rerun --install.\nLeave mounts intact for diagnosis; see --help.\n" "$stage" "$LINENO" "$rc" >&2; exit "$rc"' ERR
trap 'printf "\nInterrupted. Do not rerun --install. Inspect /mnt and cryptroot.\n" >&2; exit 130' INT TERM
wipefs -a "$disk"
sgdisk --zap-all "$disk"
sgdisk -n 1:0:+1G -t 1:ef00 -c 1:EFI -n 2:0:0 -t 2:8309 -c 2:cryptroot "$disk"
partprobe "$disk"
udevadm settle
if [[ $disk == /dev/nvme* ]]; then esp=${disk}p1; rootpart=${disk}p2
else esp=${disk}1; rootpart=${disk}2; fi
[[ -b $esp && -b $rootpart ]] || die 'New partition nodes not found.'
stage='encryption and formatting'
printf '\nCreate the DISK UNLOCK passphrase. Keep it safe; it cannot be recovered.\n'
cryptsetup luksFormat --type luks2 "$rootpart"
cryptsetup open "$rootpart" cryptroot
mkfs.fat -F 32 -n EFI "$esp"
mkfs.ext4 -L archroot /dev/mapper/cryptroot
mount /dev/mapper/cryptroot /mnt
mount --mkdir "$esp" /mnt/boot
stage='package installation (may take a while; keep internet and power connected)'
pacstrap -K /mnt "${packages[@]}"
genfstab -U /mnt > /mnt/etc/fstab
stage='system configuration'
ln -sf /usr/share/zoneinfo/Pacific/Auckland /mnt/etc/localtime
sed -i 's/^#en_NZ.UTF-8 UTF-8/en_NZ.UTF-8 UTF-8/; s/^#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /mnt/etc/locale.gen
printf 'LANG=en_NZ.UTF-8\n' > /mnt/etc/locale.conf
printf 'KEYMAP=%s\n' "$keymap" > /mnt/etc/vconsole.conf
printf 'air\n' > /mnt/etc/hostname
printf '127.0.0.1 localhost\n::1 localhost\n127.0.1.1 air.localdomain air\n' > /mnt/etc/hosts
mkdir -p /mnt/etc/mkinitcpio.conf.d /mnt/etc/systemd/logind.conf.d
printf 'HOOKS=(base systemd autodetect microcode modconf kms keyboard sd-vconsole block sd-encrypt filesystems fsck)\n' > /mnt/etc/mkinitcpio.conf.d/grey-encrypted.conf
printf '[Login]\nHandleLidSwitch=ignore\nHandleLidSwitchExternalPower=ignore\nHandleLidSwitchDocked=ignore\n' > /mnt/etc/systemd/logind.conf.d/20-grey-lid.conf
arch-chroot /mnt locale-gen
arch-chroot /mnt hwclock --systohc
arch-chroot /mnt systemctl enable NetworkManager.service systemd-timesyncd.service
arch-chroot /mnt useradd -m -G wheel -s /bin/bash grey
printf '%%wheel ALL=(ALL:ALL) ALL\n' > /mnt/etc/sudoers.d/10-grey-wheel
chmod 440 /mnt/etc/sudoers.d/10-grey-wheel
arch-chroot /mnt visudo -cf /etc/sudoers
printf '\nSet the LOGIN/SUDO password for grey (separate from disk unlock).\n'
arch-chroot /mnt passwd grey
arch-chroot /mnt passwd -l root
stage='kernel modules and initramfs validation'
# A successful pacstrap alone does not prove the DKMS hooks succeeded.
for moddir in /mnt/usr/lib/modules/*; do
  [[ -d $moddir ]] || continue
  kernel=${moddir##*/}
  arch-chroot /mnt dkms autoinstall -k "$kernel"
  arch-chroot /mnt modinfo -k "$kernel" wl >/dev/null
done
arch-chroot /mnt mkinitcpio -P
stage='bootloader'
luks_uuid=$(cryptsetup luksUUID "$rootpart")
[[ $luks_uuid =~ ^[a-fA-F0-9-]+$ && ${#luks_uuid} -eq 36 ]] || die 'Invalid LUKS UUID.'
# Standard fallback EFI path is installed even without NVRAM writes.
arch-chroot /mnt bootctl --esp-path=/boot install --no-variables
mkdir -p /mnt/boot/loader/entries
printf 'default arch.conf\ntimeout 5\neditor no\n' > /mnt/boot/loader/loader.conf
for flavor in linux linux-lts; do
  entry=arch
  [[ $flavor == linux ]] || entry=arch-lts
  printf 'title Arch (%s)\nlinux /vmlinuz-%s\ninitrd /initramfs-%s.img\noptions rd.luks.name=%s=cryptroot root=/dev/mapper/cryptroot rw\n' \
    "$flavor" "$flavor" "$flavor" "$luks_uuid" > "/mnt/boot/loader/entries/$entry.conf"
  [[ -s /mnt/boot/vmlinuz-$flavor && -s /mnt/boot/initramfs-$flavor.img ]] || die "Missing boot image for $flavor"
done
[[ -s /mnt/boot/EFI/BOOT/BOOTX64.EFI ]] || die 'Missing firmware fallback bootloader.'
stage='Codex handoff'
mkdir -p /mnt/home/grey/setup
cat > /mnt/home/grey/install-codex.sh <<'CODEX'
#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -ne 0 ]] || { echo 'Run as grey, not root or sudo.'; exit 1; }
# Official npm package, user-local prefix: no sudo npm and no curl|sh.
npm install --global --prefix "$HOME/.local" @openai/codex
"$HOME/.local/bin/codex" --version
printf '\nNext: ~/.local/bin/codex login --device-auth\nThen: cd ~/setup && ~/.local/bin/codex\n'
CODEX
chmod 700 /mnt/home/grey/install-codex.sh
cat > /mnt/home/grey/setup/HANDOFF.md <<'HANDOFF'
# Grey's Air: inspect first, preserve preferences
New encrypted Arch install on MacBookAir7,2, 8 GB. Apple app builds/Xcode
belong on the M1 iMac. Laptop is for portable coding and web/Rust work.
First verify boot, NetworkManager, wl DKMS for BOTH normal/LTS kernels,
Wi-Fi after reboot, sudo, and user-local Codex. Do not repartition.
Root is ext4 inside LUKS2; EFI mounted /boot; systemd-boot fallback path.
No quiet/splash. Passwords were entered locally, not saved by installer.
Read /etc/fstab and actual hardware before making any changes.
Back up the LUKS header onto separate offline media; never upload it.

## Restore real Zsh, not a generic replacement
Source repository: https://github.com/greysullivan/dotfiles (master)
Original .zshrc Git blob SHA: 58cfef7453dbf8c1dae71edea33bd714f39c42e9
Clone into a NEW directory; inspect before copying anything into home.
Do not execute repo scripts or source .secrets. Never echo credentials.
Preserve autosuggestions, tab menu/fuzzy matching, history substring search,
fzf + fd, zoxide, navigation aliases and Starship if wanted.
Install dependencies; fix compinit cache/path ordering, audit plugin loading,
review the 20-character suggestion cutoff with Grey. Do not copy the final
recursive cache-deletion cleanup alias into active configuration.
Old GUI/script aliases need dependency/path review; preserve original backup.
Syntax-check and interactively test Zsh before chsh. Keep Bash as fallback.

## Desktop later
X11 + i3, no display manager, TTY login and initially manual startx.
XFCE4 Terminal on Super+Space, Kitty only for rich TUIs/ncspot.
Picom sole compositor, Flameshot, libinput gestures if wanted.
Matte black/lavender/white-steel. Avoid installing a complete XFCE group.
If moving to Zsh, any optional tty1 startx guard belongs in .zprofile,
not the old PDF's .bash_profile. Do not enable until core tests pass.
Consider 4 GB zram; test power tuning rather than stacking managers.
Battery percentage should use last full capacity, not factory design capacity.
Suspend is NOT certified: lid actions intentionally ignored for now.
Test on AC/battery before enabling lid suspend; do not hibernate.
No SSH server or remote desktop enabled by this installer.
Ask before destructive changes; keep normal Codex sandbox/approval checks.
HANDOFF
arch-chroot /mnt chown -R grey:grey /home/grey/setup /home/grey/install-codex.sh
stage='final verification'
arch-chroot /mnt findmnt --verify --verbose
arch-chroot /mnt dkms status
printf '\nInstalled boot entries:\n'
cat /mnt/boot/loader/entries/*.conf
sync
umount -R /mnt
cryptsetup close cryptroot
trap - ERR INT TERM
printf '\nINSTALLATION FINISHED (hardware boot/Wi-Fi not yet tested).\n'
printf 'Run reboot; remove the ISO USB during restart. Choose EFI Boot if needed.\n'
printf 'Unlock disk, log in as grey, run nmtui, then bash ~/install-codex.sh\n'
printf 'Read --help for sign-in, recovery and the Codex handoff.\n'
