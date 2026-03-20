#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/opt/kblight"
BIN_LINK="/usr/local/bin/kblight"
DESKTOP_FILE="/usr/share/applications/kblight.desktop"
SLEEP_HOOK="/usr/lib/systemd/system-sleep/kblight"

# Ensure we can run sudo
if ! sudo -v 2>/dev/null; then
    echo "Error: This script requires sudo privileges. Please run with sudo or ensure sudo access."
    exit 1
fi

# Resolve the real user (even if running under sudo)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo "~$REAL_USER")
MONITOR_SERVICE_DIR="$REAL_HOME/.config/systemd/user"
MONITOR_SERVICE="$MONITOR_SERVICE_DIR/kblight-monitor.service"

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

if ! python3 -c "from gi.repository import Gio, GLib" &> /dev/null; then
    echo "  Installing python3-gi (PyGObject for DBus monitor)..."
    sudo apt-get install -y python3-gi gir1.2-glib-2.0
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
sudo cp "$SCRIPT_DIR/kblight-monitor.py" "$INSTALL_DIR/kblight-monitor.py"
sudo cp "$SCRIPT_DIR/ectool" "$INSTALL_DIR/ectool"
sudo cp "$SCRIPT_DIR/kblight_icon.png" "$INSTALL_DIR/kblight_icon.png"
sudo chmod +x "$INSTALL_DIR/kblight.py" "$INSTALL_DIR/kblight-monitor.py" "$INSTALL_DIR/ectool"
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
Icon=/opt/kblight/kblight_icon.png
Type=Application
Categories=Utility;Settings;HardwareSettings;
Keywords=keyboard;backlight;rgb;light;
StartupWMClass=kblight
EOF
echo "  Desktop entry created"

# Systemd service (runs as the installing user to read their config)
SERVICE_FILE="/etc/systemd/system/kblight.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Keyboard Backlight Setup
After=multi-user.target

[Service]
Type=oneshot
User=$REAL_USER
ExecStart=$INSTALL_DIR/kblight.py --restore
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kblight.service
echo "  Systemd service enabled"

# Sleep/wake hook — turns backlight off on suspend, restores on wake
sudo tee "$SLEEP_HOOK" > /dev/null <<EOF
#!/bin/bash
case "\$1" in
  pre)
    $INSTALL_DIR/ectool rgbkbd clear 0
    ;;
  post)
    su $REAL_USER -c "$INSTALL_DIR/kblight.py --restore"
    ;;
esac
EOF
sudo chmod +x "$SLEEP_HOOK"
echo "  Sleep/wake hook installed"

# Screen lock/unlock monitor (systemd user service)
# Uses DBus to detect screen lock and toggle backlight
mkdir -p "$MONITOR_SERVICE_DIR"
cat > "$MONITOR_SERVICE" <<EOF
[Unit]
Description=Keyboard Backlight Screen Lock Monitor
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/kblight-monitor.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
EOF
chown "$REAL_USER:$REAL_USER" "$MONITOR_SERVICE"

# Enable and start as the real user
su "$REAL_USER" -c "systemctl --user daemon-reload"
su "$REAL_USER" -c "systemctl --user enable --now kblight-monitor.service"
echo "  Screen lock monitor service enabled"

echo ""
echo "Done! You can now:"
echo "  - Search 'KB Backlight' in your app launcher"
echo "  - Run 'kblight' from the terminal"
echo "  - Settings are restored automatically at boot and after sleep"
echo "  - Backlight turns off/on automatically when the screen locks/unlocks"
