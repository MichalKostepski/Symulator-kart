"""Non-interactive Tkinter startup check and optional real GUI screenshots.

Run this script only on a machine with a graphical display (or under Xvfb).
It deliberately mocks network connections: no participants or secrets are needed.
"""
import argparse
import sys
import time
import tkinter as tk
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1] / "app"
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from host_gui import HostGuiApp
from client import CardGameClientApp


def capture(name, cls, patch_method, output_dir):
    root = tk.Tk()
    app = None
    try:
        with patch.object(cls, patch_method, return_value=False):
            app = cls(root)
        root.update_idletasks()
        assert root.winfo_exists(), f"{name}: window was not created"
        assert root.winfo_width() > 500 and root.winfo_height() > 400, (
            f"{name}: unexpected window dimensions"
        )
        if name == "host":
            assert {"POKER", "MAKAO"} <= set(app.games), "Host must expose both games"
        else:
            assert app.active_game is None and not app.connected
            assert app.menu_stats_var is not None

        if output_dir is not None:
            # Screenshot contains only fictional/empty local UI state.
            from PIL import ImageGrab

            time.sleep(0.25)
            root.update_idletasks()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            w, h = root.winfo_width(), root.winfo_height()
            output_dir.mkdir(parents=True, exist_ok=True)
            shot = output_dir / f"{name}-window.png"
            ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(shot)
            print(f"Saved authentic Tkinter screenshot: {shot}")

        print(f"PASS: {name} GUI instantiated and sized correctly")
    finally:
        if app is not None:
            app.running = False
        root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--screenshots", type=Path, default=None, metavar="DIR",
        help="Capture actual Tk windows. Requires Pillow and an X11 display.",
    )
    args = parser.parse_args()
    capture("host", HostGuiApp, "start_server", args.screenshots)
    capture("client", CardGameClientApp, "connect_to_server", args.screenshots)


if __name__ == "__main__":
    main()
