#!/usr/bin/env python3
"""GUI and CLI wrapper for ectool rgbkbd keyboard backlight control.

Usage:
  kblight                          Launch GUI
  kblight --color white            Set a preset color
  kblight --color 255,128,0        Set RGB color
  kblight --brightness 80          Set brightness (0-100)
  kblight --color red --brightness 50   Both at once
  kblight --off                    Turn off backlight
  kblight --restore                Restore last saved settings (used at boot)
"""

import argparse
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ECTOOL = os.path.join(SCRIPT_DIR, "ectool")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "kblight.json")

PRESETS = {
    "white":  (255, 255, 255),
    "red":    (255, 0,   0),
    "green":  (0,   255, 0),
    "blue":   (0,   0,   255),
    "cyan":   (0,   255, 255),
    "purple": (255, 0,   255),
    "yellow": (255, 255, 0),
    "orange": (255, 136, 0),
}


def load_config():
    """Load saved config, returning defaults if not found."""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"color": [255, 255, 255], "brightness": 100}


def save_config(color=None, brightness=None):
    """Save current settings to config file."""
    config = load_config()
    if color is not None:
        config["color"] = list(color)
    if brightness is not None:
        config["brightness"] = brightness
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def rgb_to_ectool_value(r, g, b):
    """Convert RGB (0-255) to ectool packed decimal color string."""
    return str((r << 16) | (g << 8) | b)


def rgb_to_hex(r, g, b):
    """Convert RGB 0-255 to hex string for tkinter."""
    return f"#{r:02x}{g:02x}{b:02x}"


def set_color(r, g, b):
    """Set keyboard backlight color via ectool and save."""
    value = rgb_to_ectool_value(r, g, b)
    cmd = ["sudo", ECTOOL, "rgbkbd", "clear", value]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"ectool error: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"ectool not found at {ECTOOL}", file=sys.stderr)
        return False
    save_config(color=(r, g, b))
    return True


def set_brightness(val):
    """Set keyboard brightness via ectool pwmsetkblight and save."""
    cmd = ["sudo", ECTOOL, "pwmsetkblight", str(val)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"ectool error: {e.stderr}", file=sys.stderr)
        return False
    save_config(brightness=int(val))
    return True


def parse_color(color_str):
    """Parse a color string: preset name or R,G,B."""
    if color_str.lower() in PRESETS:
        return PRESETS[color_str.lower()]
    parts = color_str.split(",")
    if len(parts) == 3:
        try:
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            if all(0 <= c <= 255 for c in (r, g, b)):
                return (r, g, b)
        except ValueError:
            pass
    print(f"Invalid color: '{color_str}'. Use a preset name ({', '.join(PRESETS)}) or R,G,B (0-255).",
          file=sys.stderr)
    sys.exit(1)


def restore():
    """Restore last saved settings."""
    config = load_config()
    r, g, b = config["color"]
    set_color(r, g, b)
    set_brightness(config["brightness"])


def run_cli(args):
    """Handle CLI mode."""
    if args.restore:
        restore()
        return

    if args.off:
        set_brightness(0)
        return

    if args.color:
        r, g, b = parse_color(args.color)
        set_color(r, g, b)

    if args.brightness is not None:
        set_brightness(args.brightness)


def run_gui():
    """Launch the GUI."""
    import tkinter as tk
    from tkinter import colorchooser

    config = load_config()

    def update_preview(r, g, b):
        hex_color = rgb_to_hex(r, g, b)
        preview.config(bg=hex_color)
        ectool_val = rgb_to_ectool_value(r, g, b)
        hex_label.config(text=ectool_val, bg=hex_color,
                         fg="black" if (r + g + b) > 380 else "white")

    def pick_color():
        color = colorchooser.askcolor(title="Pick Keyboard Color")
        if color[0]:
            r, g, b = [int(c) for c in color[0]]
            set_color(r, g, b)
            update_preview(r, g, b)

    def apply_preset(r, g, b):
        set_color(r, g, b)
        update_preview(r, g, b)

    def turn_off():
        brightness_slider.set(0)

    def on_brightness(val):
        set_brightness(val)

    root = tk.Tk()
    root.title("KB Backlight")
    root.resizable(False, False)

    init_r, init_g, init_b = config["color"]
    init_hex = rgb_to_hex(init_r, init_g, init_b)

    preview = tk.Frame(root, width=200, height=80, bg=init_hex, relief="sunken", bd=2)
    preview.pack(padx=10, pady=(10, 5))
    preview.pack_propagate(False)

    hex_label = tk.Label(preview, text=rgb_to_ectool_value(init_r, init_g, init_b),
                         bg=init_hex, font=("monospace", 14),
                         fg="black" if (init_r + init_g + init_b) > 380 else "white")
    hex_label.pack(expand=True)

    tk.Button(root, text="Pick Color...", command=pick_color, width=20).pack(pady=5)

    preset_frame = tk.LabelFrame(root, text="Presets", padx=5, pady=5)
    preset_frame.pack(padx=10, pady=5, fill="x")

    preset_list = [
        ("White",  255, 255, 255),
        ("Red",    255, 0,   0),
        ("Green",  0,   255, 0),
        ("Blue",   0,   0,   255),
        ("Cyan",   0,   255, 255),
        ("Purple", 255, 0,   255),
        ("Yellow", 255, 255, 0),
        ("Orange", 255, 136, 0),
    ]

    for i, (name, r, g, b) in enumerate(preset_list):
        btn = tk.Button(
            preset_frame,
            text=name,
            bg=rgb_to_hex(r, g, b),
            fg="black" if (r + g + b) > 380 else "white",
            width=8,
            command=lambda r=r, g=g, b=b: apply_preset(r, g, b),
        )
        btn.grid(row=i // 4, column=i % 4, padx=2, pady=2)

    bright_frame = tk.LabelFrame(root, text="Brightness", padx=5, pady=5)
    bright_frame.pack(padx=10, pady=5, fill="x")

    brightness_slider = tk.Scale(bright_frame, from_=0, to=100, orient="horizontal", command=on_brightness)
    brightness_slider.set(config["brightness"])
    brightness_slider.pack(fill="x")

    tk.Button(root, text="Off", command=turn_off, width=20, bg="#333333", fg="white").pack(pady=(5, 10))

    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Keyboard backlight control")
    preset_names = ", ".join(PRESETS.keys())
    parser.add_argument("--color", "-c",
                        help=f"Color: preset name ({preset_names}) or R,G,B (0-255)")
    parser.add_argument("--brightness", "-b", type=int, help="Brightness 0-100")
    parser.add_argument("--off", action="store_true", help="Turn off backlight")
    parser.add_argument("--restore", action="store_true", help="Restore last saved settings")
    args = parser.parse_args()

    if args.color or args.brightness is not None or args.off or args.restore:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
