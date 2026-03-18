#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/kblight"
BIN_LINK="/usr/local/bin/kblight"
DESKTOP_FILE="/usr/share/applications/kblight.desktop"

# Ensure we can run sudo
if ! sudo -v 2>/dev/null; then
    echo "Error: This script requires sudo privileges. Please run with sudo or ensure sudo access."
    exit 1
fi

echo "Installing kblight..."

# Check/install dependencies
if ! command -v python3 &> /dev/null; then
    echo "  Installing python3..."
    sudo apt-get install -y python3
fi

if ! python3 -c "import tkinter" &> /dev/null; then
    echo "  Installing python3-tk..."
    sudo apt-get install -y python3-tk
fi

echo "  Dependencies OK"

# Allow ectool to run without password prompt (needed for GUI/desktop use)
SUDOERS_FILE="/etc/sudoers.d/kblight"
sudo tee "$SUDOERS_FILE" > /dev/null <<EOF
ALL ALL=(root) NOPASSWD: $INSTALL_DIR/ectool
EOF
sudo chmod 0440 "$SUDOERS_FILE"
echo "  Sudoers rule added for ectool"

# Copy files to /opt/kblight
sudo mkdir -p "$INSTALL_DIR"
sudo cp "$SCRIPT_DIR/kblight.py" "$INSTALL_DIR/kblight.py"
sudo cp "$SCRIPT_DIR/ectool" "$INSTALL_DIR/ectool"
sudo chmod +x "$INSTALL_DIR/kblight.py" "$INSTALL_DIR/ectool"
echo "  Installed to $INSTALL_DIR"

# Symlink to PATH
sudo ln -sf "$INSTALL_DIR/kblight.py" "$BIN_LINK"
echo "  Linked $BIN_LINK"

# Desktop entry
sudo tee "$DESKTOP_FILE" > /dev/null <<'EOF'
[Desktop Entry]
Name=KB Backlight
Comment=Keyboard backlight color and brightness control
Exec=/opt/kblight/kblight.py
Icon=preferences-desktop-keyboard
Type=Application
Categories=Utility;Settings;HardwareSettings;
Keywords=keyboard;backlight;rgb;light;
EOF
echo "  Desktop entry created"

# Systemd service
SERVICE_FILE="/etc/systemd/system/kblight.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Keyboard Backlight Setup
After=multi-user.target

[Service]
Type=oneshot
ExecStart=$INSTALL_DIR/kblight.py --restore
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kblight.service
echo "  Systemd service enabled"

echo ""
echo "Done! You can now:"
echo "  - Search 'KB Backlight' in your app launcher"
echo "  - Run 'kblight' from the terminal"
echo "  - Settings are restored automatically at boot"
