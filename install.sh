#!/bin/bash
set -e

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run as root (e.g., sudo ./install.sh)"
  exit 1
fi

echo "========================================="
echo " Installing facer-gui  "
echo "========================================="

# 1. Verify facer-rgb CLI tool presence
if ! command -v facer-rgb &> /dev/null; then
    echo "Warning: 'facer-rgb' CLI tool was not found in system PATH."
    echo "Ensure facer-rgb driver binary is placed in /usr/local/bin or /usr/bin."
fi

# 2. Install main Python executable
echo "[1/7] Copying application binary to /usr/local/bin/facer-gui..."
cp main.py /usr/local/bin/facer-gui
chmod +x /usr/local/bin/facer-gui

# 3. Configure udev rules for non-root hardware access
echo "[2/7] Setting up udev rules for /dev/acer-gkbbl-0..."
echo 'KERNEL=="acer-gkbbl-0", MODE="0666"' > /etc/udev/rules.d/99-acer-gkbbl.rules
udevadm control --reload-rules && udevadm trigger

# 4. Ensure kernel driver auto-loads at boot
echo "[3/7] Setting up kernel module auto-load..."
echo "acer_wmi" > /etc/modules-load.d/acer-gkbbl.conf

# 5. Seed baseline config
echo "[4/7] Seeding default configuration..."
DEFAULT_CONFIG='{
    "mode": 0,
    "mode_name": "Static",
    "speed": 5,
    "direction": 1,
    "brightness": 100,
    "anim_color": [0, 180, 138],
    "startup_animation": true,
    "zones": {
        "1": [137, 180, 250],
        "2": [243, 139, 168],
        "3": [166, 227, 161],
        "4": [203, 166, 247]
    },
    "zone_state": {"1": true, "2": true, "3": true, "4": true}
}'

mkdir -p /etc/skel/.config
echo "$DEFAULT_CONFIG" > /etc/skel/.config/acer_rgb_hub_config.json

if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    USER_CONFIG_DIR="$USER_HOME/.config"
    mkdir -p "$USER_CONFIG_DIR"
    if [ ! -f "$USER_CONFIG_DIR/acer_rgb_hub_config.json" ]; then
        echo "$DEFAULT_CONFIG" > "$USER_CONFIG_DIR/acer_rgb_hub_config.json"
        chown -R "$SUDO_USER:" "$USER_CONFIG_DIR/acer_rgb_hub_config.json"
    fi
fi

# 6. Install desktop app launcher and XDG autostart entry
echo "[5/7] Installing desktop integration and session autostart..."
cat <<EOF > /usr/share/applications/facer-gui.desktop
[Desktop Entry]
Type=Application
Name=Facer GUI
Comment=Facer RGB Configuration
Exec=/usr/local/bin/facer-gui
Icon=input-gaming
Terminal=false
Categories=System;Settings;
EOF

cat <<EOF > /etc/xdg/autostart/facer-gui-autostart.desktop
[Desktop Entry]
Type=Application
Name=Facer GUI Autostart
Comment=Triggers Facer GUI startup on session login
Exec=/usr/local/bin/facer-gui --silent
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
EOF

# 7. Setup the Systemd Hardware Shutdown Hook
echo "[6/7] Creating hardware shutdown script (facer-red-shutdown.sh)..."
cat << 'EOF' > /usr/local/bin/facer-red-shutdown.sh
#!/bin/bash

# Dynamically locate the executable
FACER=$(command -v facer-rgb || echo "/usr/local/bin/facer-rgb")
if [ ! -x "$FACER" ]; then
    exit 0
fi

# Search for the user's GUI config to check if the animation toggle is enabled
CONFIG_FILE=$(ls /home/*/.config/acer_rgb_hub_config.json 2>/dev/null | head -n 1)

if [ -f "$CONFIG_FILE" ]; then
    ANIM_ENABLED=$(grep -o '"startup_animation": [a-z]*' "$CONFIG_FILE" | cut -d' ' -f2)
    # If the user toggled it off in the GUI, abort the shutdown wipe
    if [ "$ANIM_ENABLED" = "false" ]; then
        exit 0
    fi
fi

# Apply pure red hardware state directly without modifying the JSON config.
for z in {1..4}; do
    "$FACER" -m 0 -z $z -cR 255 -cG 0 -cB 0
done
EOF

chmod +x /usr/local/bin/facer-red-shutdown.sh

echo "[7/7] Registering systemd shutdown service..."
cat <<EOF > /etc/systemd/system/facer-rgb-shutdown.service
[Unit]
Description=Facer RGB Shutdown Hardware State Lock
After=multi-user.target

[Service]
Type=oneshot
RemainAfterExit=yes
# Dummy start command so the service is considered "active"
ExecStart=/bin/true
# The actual magic happens on stop (shutdown) while hardware interfaces are still up
ExecStop=/usr/local/bin/facer-red-shutdown.sh
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable facer-rgb-shutdown.service
systemctl start facer-rgb-shutdown.service

echo "========================================="
echo " Installation Complete!"
echo " The full animation lifecycle (Shutdown -> Boot -> Login) is now active."
echo "========================================="