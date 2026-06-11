import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

from client import CardGameClientApp

class TestClientGUI(unittest.TestCase):
    @patch("client.socket.socket")
    @patch("client.threading.Thread")
    def setUp(self, mock_thread, mock_socket):
        self.root = tk.Tk()
        with patch('client.CardGameClientApp.connect_to_server', return_value=False):
            self.app = CardGameClientApp(self.root)
        self.root.update()
        self.app.connected = False

    def tearDown(self):
        self.app.running = False
        self.root.destroy()

    def test_default_menu(self):
        self.assertIsNone(self.app.active_game)
        self.assertFalse(self.app.connected)
        self.assertEqual(self.app.status_var.get(), "Nie połączono z serwerem")

        self.assertIsNone(self.app.poker_table_canvas)
        self.assertIsNone(self.app.poker_hand_frame)
        self.assertIsNone(self.app.makao_hand_frame)
        self.assertIsNone(self.app.makao_play_button)

    @patch("client.messagebox.showinfo")
    def test_show_rules_poker(self, mock_showinfo):
        self.app.show_rules_poker()
        mock_showinfo.assert_called_once()
        self.assertIn("stole", mock_showinfo.call_args[0][1])

    @patch("client.messagebox.showinfo")
    def test_show_rules_makao(self, mock_showinfo):
        self.app.show_rules_makao()
        mock_showinfo.assert_called_once()
        self.assertIn("funkcyjne", mock_showinfo.call_args[0][1])

    @patch('tkinter.colorchooser.askcolor')
    def test_change_color(self, mock_askcolor):
        mock_askcolor.return_value = ((11, 61, 46), "#0b3d2e")
        self.app.change_color()
        self.assertEqual(self.app.bg_color, "#0b3d2e")

    @patch('client.messagebox.showwarning')
    def test_send_connection_drop(self, mock_showwarning):
        self.app.show_poker()
        self.app.connected = True
        self.app.client = MagicMock()

        self.app.client.sendall.side_effect = OSError("Connection reset by peer")

        result = self.app.send({"action": "TEST"})

        self.assertFalse(result)
        self.assertFalse(self.app.connected)
        self.assertEqual(self.app.status_var.get(), "Utracono połączenie z serwerem")

    @patch('client.recv_exact', return_value=None)
    def test_receive_loop_disconnect(self, mock_recv_exact):
        self.app.running = True
        self.app.client = MagicMock()

        self.app.receive_loop()

        self.assertFalse(self.app.connected)

        self.root.update()

        self.assertEqual(self.app.status_var.get(), "Rozłączono z serwerem")


    def test_to_poker(self):
        self.app.show_poker()
        self.root.update()

        self.assertEqual(self.app.active_game, "POKER")

        self.assertIsNotNone(self.app.poker_table_canvas)

        button_state = self.app.poker_call_button.cget("state")
        self.assertEqual(button_state, "disabled")

    def test_state_poker(self):
        self.app.show_poker()

        msg = {
            "game": "POKER",
            "type": "TABLE",
            "data": {
                "pot": 250,
                "current_bet": 50,
                "phase": "FLOP",
                "community_cards": ["AH", "3H", "6S"]
            }
        }
        self.app.handle_server_msg(msg)
        self.root.update()

        self.assertEqual(self.app.poker_pot_var.get(), "Pula: 250")
        self.assertEqual(self.app.poker_current_bet_var.get(), "Aktualny bet: 50")
        self.assertEqual(self.app.poker_phase_var.get(), "Faza: FLOP")
        self.assertEqual(len(self.app.poker_community_cards), 3)


    def test_poker_buttons(self):
        self.app.show_poker()
        self.app.my_player_id = 1

        msg = {
            "game": "POKER",
            "type": "TURN",
            "player_id": 1,
            "data": {"your_bet": 10, "current_bet": 30}
        }
        self.app.handle_server_msg(msg)
        self.root.update()

        self.assertEqual(self.app.poker_call_button.cget("state"), "normal")
        self.assertEqual(self.app.poker_fold_button.cget("state"), "normal")


    def test_makao_initiate(self):
        self.app.show_makao()
        self.root.update()

        self.assertEqual(self.app.active_game, "MAKAO")
        self.assertIsNotNone(self.app.makao_hand_frame)
        self.assertIsNotNone(self.app.makao_play_button)
        self.assertIsNotNone(self.app.makao_draw_button)


    def test_simulation_cards_makao(self):
        self.app.show_makao()

        msg = {
            "game": "MAKAO",
            "type": "HAND",
            "player_id": 1,
            "data": {"cards": ["AH", "7C", "9D"]}
        }
        self.app.handle_server_msg(msg)
        self.root.update()

        self.assertEqual(len(self.app.makao_hand_cards), 3)
        self.assertEqual(self.app.status_var.get(), "Dostałeś karty. Czekaj na swoją turę.")


    def test_makao_chose_card(self):
        self.app.show_makao()
        self.app.makao_hand_cards = ["10C", "2D"]

        self.app.selected_makao_card = "10C"
        self.app.makao_selected_card_var.set("Wybrana karta: 10C")

        self.assertEqual(self.app.selected_makao_card, "10C")
        self.assertEqual(self.app.makao_selected_card_var.get(), "Wybrana karta: 10C")


if __name__ == "__main__":
    unittest.main()