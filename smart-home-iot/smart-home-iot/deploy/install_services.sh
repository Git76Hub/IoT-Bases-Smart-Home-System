#!/usr/bin/env bash
# Installs the systemd units so everything starts on boot.
# Run from the repository root on the Pi: sudo ./deploy/install_services.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_USER="${SUDO_USER:-$USER}"
for unit in "$DIR"/deploy/*.service; do
  sed "s|__DIR__|$DIR|g; s|__USER__|$RUN_USER|g" "$unit" > "/etc/systemd/system/$(basename "$unit")"
done
systemctl daemon-reload
for name in automation dashboard serial-bridge; do
  systemctl enable --now "smarthome-$name"
done
echo "Installed. Check with: systemctl status smarthome-automation"
echo "(Skip serial-bridge if no Arduino is attached: sudo systemctl disable --now smarthome-serial-bridge)"
