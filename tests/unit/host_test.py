import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk

from host_gui import HostGuiApp

class TestHostGUI(unittest.TestCase):
	def setUp(self):
		self.root = tk.Tk()
		with patch.object(HostGuiApp, 'start_server', return_value=None):
			self.app = HostGuiApp(self.root)
		self.root.update()

	def tearDown(self):
		self.app.running = False
		self.root.destroy()
		if self.app.server_socket:
			self.app.server_socket.close()

	def test_add_bot(self):
		start = self.app.poker_bots_var.get()
		self.assertEqual(start, "Boty: 0")

		self.app.add_bot("POKER")
		self.root.update()

		end = self.app.poker_bots_var.get()
		self.assertEqual(end, "Boty: 1")

	def test_start_no_players(self):
		self.app.start_game("MAKAO")
		self.root.update()

		status = self.app.makao_phase_var.get()
		self.assertEqual(status, "Status: waiting")

		self.app.start_game("POKER")
		self.root.update()

		status = self.app.makao_phase_var.get()
		self.assertEqual(status, "Status: waiting")

	def test_players_count(self):
		self.app.add_bot("POKER")
		self.app.add_bot("POKER")
		self.root.update()

		players = self.app.poker_players_var.get()
		self.assertEqual(players, "Gracze: 2")

	@patch('host_gui.recv_exact')
	def test_client_sudden_disconnect_during_game(self, mock_recv_exact):
		mock_conn = MagicMock()
		mock_addr = ("192.168.1.10", 55555)

		join_payload = b'{"game": "SYSTEM", "type": "JOIN", "data": {"target_game": "POKER"}}'
		header = str(len(join_payload)).encode('utf-8').ljust(64, b' ')

		mock_recv_exact.side_effect = [header, join_payload, None]

		with patch.object(self.app.games["POKER"], 'remove_player') as mock_remove:
			self.app.handle_client(mock_conn, mock_addr)
			mock_remove.assert_called_once()
			mock_conn.close.assert_called_once()

	@patch('host_gui.send_json')
	@patch('host_gui.recv_exact')
	def test_join_full_room_exception(self, mock_recv_exact, mock_send_json):
		mock_conn = MagicMock()
		mock_addr = ("127.0.0.1", 12345)

		join_payload = b'{"game": "SYSTEM", "type": "JOIN", "data": {"target_game": "POKER"}}'
		header = str(len(join_payload)).encode('utf-8').ljust(64, b' ')

		mock_recv_exact.side_effect = [header, join_payload, None]

		with patch.object(self.app.games["POKER"], 'add_player', side_effect=Exception("Pokój jest pełny")):
			self.app.handle_client(mock_conn, mock_addr)
			mock_conn.close.assert_called_once()

if __name__ == "__main__":
	unittest.main()