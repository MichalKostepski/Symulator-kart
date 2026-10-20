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

import host_gui
import client
from host_gui import HostGuiApp
from client import CardGameClientApp


def prepare_fictional_poker_preview(app):
    """Render a fictional example directly through the genuine player UI."""
    app.my_player_id = 1
    app.poker_hand_cards = ["AH", "KD"]
    app.poker_community_cards = ["7H", "2C", "QS"]
    app.poker_phase = "flop"
    app.poker_pot = 180
    app.poker_current_bet = 20
    app.poker_your_bet = 20
    app.poker_turn_player = 1
    app.poker_blind_player = 2
    app.poker_players = [
        {"player_id": 1, "is_bot": False, "chips": 480, "bet": 20, "folded": False, "all_in": False},
        {"player_id": 2, "is_bot": True, "chips": 460, "bet": 20, "folded": False, "all_in": False},
        {"player_id": 3, "is_bot": True, "chips": 470, "bet": 20, "folded": False, "all_in": False},
    ]
    app.status_var.set("WIDOK DEMO - fikcyjny stan, bez polaczenia z serwerem")
    app.show_poker()
    app.poker_chips_var.set("Zetony: 480")
    app.set_poker_action_buttons(False)
    app.root.update_idletasks()
    app.root.update()
    app.draw_poker_table()


def capture(name, cls, patch_method, output_dir):
    root = tk.Tk()
    app = None
    try:
        with patch.object(cls, patch_method, return_value=False), (
            patch.object(host_gui, "DEFAULT_SERVER", "127.0.0.1")
        ), patch.object(client, "DEFAULT_SERVER", "127.0.0.1"):
            app = cls(root)
        root.update_idletasks()
        # Xvfb needs one full event-loop pass to paint button and label text.
        root.update()
        assert root.winfo_exists(), f"{name}: window was not created"
        assert root.winfo_width() > 500 and root.winfo_height() > 400, (
            f"{name}: unexpected window dimensions"
        )
        if name == "host":
            assert {"POKER", "MAKAO"} <= set(app.games), "Host must expose both games"
        else:
            assert app.active_game is None and not app.connected
            assert app.menu_stats_var is not None

        if name == "poker-demo":
            prepare_fictional_poker_preview(app)

        if output_dir is not None:
            # GUI and any player state are genuine Tk widgets with fictional examples.
            from PIL import ImageGrab

            time.sleep(0.35)
            root.update()
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
    capture("poker-demo", CardGameClientApp, "connect_to_server", args.screenshots)


if __name__ == "__main__":
    main()
