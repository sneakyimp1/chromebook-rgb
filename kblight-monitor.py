#!/usr/bin/env python3
"""Monitor screen lock/unlock via DBus and toggle keyboard backlight.

Listens for ActiveChanged signals from both org.gnome.ScreenSaver and
org.freedesktop.ScreenSaver, so it works on GNOME, KDE, and other
freedesktop-compliant desktops.
"""

import os
import subprocess
import sys

from gi.repository import Gio, GLib

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ECTOOL = os.path.join(SCRIPT_DIR, "ectool")
KBLIGHT = os.path.join(SCRIPT_DIR, "kblight.py")


def on_screen_locked():
    """Turn off keyboard backlight (without saving to config)."""
    try:
        subprocess.run(
            ["sudo", ECTOOL, "rgbkbd", "clear", "0"],
            capture_output=True, check=True,
        )
    except Exception as e:
        print(f"Failed to turn off backlight: {e}", file=sys.stderr)


def on_screen_unlocked():
    """Restore keyboard backlight from saved config."""
    try:
        subprocess.run(
            [KBLIGHT, "--restore"],
            capture_output=True, check=True,
        )
    except Exception as e:
        print(f"Failed to restore backlight: {e}", file=sys.stderr)


def on_signal(connection, sender, path, interface, signal, params):
    """Handle ActiveChanged signal from screensaver DBus interfaces."""
    active = params.unpack()[0]
    if active:
        on_screen_locked()
    else:
        on_screen_unlocked()


def main():
    bus = Gio.bus_get_sync(Gio.BusType.SESSION)

    # Subscribe to both GNOME and freedesktop screensaver signals
    for iface in ("org.gnome.ScreenSaver", "org.freedesktop.ScreenSaver"):
        bus.signal_subscribe(
            None,           # sender
            iface,          # interface
            "ActiveChanged",  # signal
            None,           # object path
            None,           # arg0
            Gio.DBusSignalFlags.NONE,
            on_signal,
        )

    print("Monitoring screen lock/unlock for keyboard backlight control...")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()


if __name__ == "__main__":
    main()
