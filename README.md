# Chromebook RGB Keyboard

A simple GUI and CLI tool for controlling the RGB keyboard backlight on Chromebooks (and other ChromeOS EC-based laptops like Framework) using `ectool`.

## Features

- **GUI** with color picker, preset colors, and brightness slider
- **CLI** for scripting and automation
- **Persistent settings** - saves last used color and brightness to `~/.config/kblight/`
- **Auto-restore at boot** via systemd service
- **App launcher integration** - shows up in your desktop environment

## Dependencies

- Python 3
- python3-tk
- `ectool` binary (ChromeOS EC tool with `rgbkbd` support) - included in this repo

## Install

```bash
git clone https://github.com/sneakyimp1/chromebook-rgb.git
cd chromebook-rgb
bash install.sh
```

The install script requires sudo and will:
- Install dependencies (python3, python3-tk) if missing
- Copy files to `/opt/kblight/`
- Add `kblight` command to your PATH
- Add a sudoers rule so `ectool` can run without a password prompt (required for GUI/app launcher use)
- Create a desktop entry ("KB Backlight" in your app launcher)
- Enable a systemd service to restore your settings at boot

## Usage

### GUI

Launch from your app launcher by searching "KB Backlight", or run:
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
sudo rm -rf /opt/kblight /usr/local/bin/kblight /usr/share/applications/kblight.desktop /etc/systemd/system/kblight.service /etc/sudoers.d/kblight
```
