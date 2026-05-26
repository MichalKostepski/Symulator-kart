from poker import PokerGame
from card_simple import CardSimple
from deck_simple import DeckSimple
import unittest
from unittest.mock import MagicMock

class TestPokerLogic(unittest.TestCase):
	def setUp(self):
		self.mock_send = MagicMock()
		self.mock_create_msg = MagicMock(side_effect=lambda *args, **kwargs: kwargs)

		self.game = PokerGame(self.mock_send, self.mock_create_msg)

		self.player_ids = []
		for addr in ["addr1", "addr2", "addr3"]:
			pid = self.game.add_player(MagicMock(), addr)
			self.player_ids.append(pid)

		self.p1, self.p2, self.p3 = self.player_ids

		self.game.game_state["game_started"] = True
		self.game.game_state["phase"] = "pre-flop"
		self.game.game_state["current_bet"] = 20
		self.game.game_state["pot"] = 30
		self.game.game_state["current_turn"] = 1

	def test_fold_action(self):
		msg = {
			"type": "MOVE",
			"player_id": self.p2,
			"data": {"action": "FOLD"}
		}
		self.game.handle_message(msg)

		expected_index = next(i for i, (pid, _, _) in enumerate(self.game.players) if pid == self.p3)
		self.assertIn(self.p2, self.game.game_state["folded_players"])
		self.assertEqual(self.game.game_state["current_turn"], expected_index)

	def test_raise_action(self):
		player_id = self.p2
		initial_chips = self.game.game_state["chips"][player_id]
		raise_amount = 50

		msg = {
			"type": "MOVE",
			"player_id": player_id,
			"data": {"action": "RAISE", "amount": raise_amount}
		}
		self.game.handle_message(msg)

		self.assertEqual(self.game.game_state["chips"][player_id], initial_chips - raise_amount)
		self.assertEqual(self.game.game_state["current_bet"], raise_amount)
		self.assertEqual(self.game.game_state["pot"], 30 + raise_amount)

	def test_phase_advancement(self):
		self.game.game_state["current_bet"] = 20
		self.game.game_state["round_bets"] = {
			self.p1: 20, self.p2: 20, self.p3: 20
		}
		self.game.game_state["players_acted"] = {self.p1, self.p2, self.p3}

		is_over = self.game.is_betting_round_over()
		self.assertTrue(is_over)

	def test_bankruptcy(self):
		self.game.game_state["chips"][self.p1] = 0
		self.game.handle_bancruptcies()

		self.mock_send.assert_called()

	def test_raise_more_than_chips(self):
		player_id = self.p2
		starting_chips = 100
		self.game.game_state["chips"][player_id] = starting_chips
		self.game.game_state["current_bet"] = 20
		self.game.game_state["pot"] = 40
		self.game.game_state["current_turn"] = 1

		illegal_amount = 200
		msg = {
			"type": "MOVE",
			"player_id": player_id,
			"data": {"action": "RAISE", "amount": illegal_amount}
		}
		self.game.handle_message(msg)

		self.assertEqual(self.game.game_state["chips"][player_id], starting_chips)
		self.assertEqual(self.game.game_state["pot"], 40)
		self.assertEqual(self.game.game_state["current_turn"], 1)

if __name__ == "__main__":
	unittest.main()