# Chromebook RGB Keyboard

A simple GUI and CLI tool for controlling the RGB keyboard backlight on Chromebooks (and other ChromeOS EC-based laptops like Framework) using `ectool`.

## Features

- **GUI** with color picker, preset colors, and brightness slider
- **CLI** for scripting and automation
- **Persistent settings** - saves last used color and brightness
- **Auto-restore at boot** via systemd service
- **App launcher integration** - shows up in your desktop environment

## Dependencies

- Python 3
- python3-tk
- `ectool` binary (ChromeOS EC tool with `rgbkbd` support) - included in this repo

## Install

```bash
bash install.sh
```

This will:
- Install dependencies (python3, python3-tk)
- Copy files to `/opt/kblight/`
- Add `kblight` command to your PATH
- Create a desktop entry ("KB Backlight" in your app launcher)
- Enable a systemd service to restore your settings at boot

## Usage

### GUI
```bash
kblight
```

### CLI
```bash
kblight --color white            # Set a preset color
kblight --color 255,128,0        # Set custom RGB color (0-255 per channel)
kblight --brightness 80          # Set brightness (0-100)
kblight --color red --brightness 50   # Both at once
kblight --off                    # Turn off backlight
kblight --restore                # Restore last saved settings
```

### Available preset colors

white, red, green, blue, cyan, purple, yellow, orange

## Uninstall

```bash
sudo systemctl disable kblight.service
sudo rm -rf /opt/kblight /usr/local/bin/kblight /usr/share/applications/kblight.desktop /etc/systemd/system/kblight.service
```
