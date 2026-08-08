#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

echo "========================================="
echo " Uninstalling NitroRGB GUI & Integration "
echo "========================================="

# 1. Stop and disable Systemd Shutdown Service
if systemctl is-active --quiet nitro-rgb-shutdown.service 2>/dev/null || systemctl is-enabled --quiet nitro-rgb-shutdown.service 2>/dev/null; then
    echo "[1/5] Disabling and stopping nitro-rgb-shutdown.service..."
    systemctl stop nitro-rgb-shutdown.service 2>/dev/null || true
    systemctl disable nitro-rgb-shutdown.service 2>/dev/null || true
    rm -f /etc/systemd/system/nitro-rgb-shutdown.service
    systemctl daemon-reload
else
    echo "[1/5] Systemd shutdown service not active, skipping..."
fi

# 2. Remove Executables & Scripts
echo "[2/5] Removing installed binaries..."
rm -f /usr/local/bin/nitrorgb
rm -f /usr/local/bin/nitro-red-shutdown.sh

# 3. Remove Desktop Launchers & Autostart
echo "[3/5] Removing application launchers..."
rm -f /usr/share/applications/nitrorgb.desktop
rm -f /etc/xdg/autostart/nitrorgb-autostart.desktop

# 4. Remove Udev Rules & Kernel Auto-load Config
echo "[4/5] Removing udev rules and module autoload configs..."
rm -f /etc/udev/rules.d/99-acer-gkbbl.rules
rm -f /etc/modules-load.d/acer-gkbbl.conf
udevadm control --reload-rules && udevadm trigger

# 5. Clean up skeleton default config (optional: leaves user ~/.config untouched)
echo "[5/5] Removing skeleton configuration..."
rm -f /etc/skel/.config/nitro_rgb_config.json

echo "========================================="
echo " Uninstall Complete!"
echo " Note: 'facer-rgb' driver and kernel modules were left intact."
echo "========================================="