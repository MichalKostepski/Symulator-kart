import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

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

	def test_phase_end(self):
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

	def test_evaluate_5cards_all_hands(self):
		res, *_ = self.game.evaluate_5cards(['10H', 'JH', 'QH', 'KH', 'AH'])
		self.assertEqual(res, 8)

		res, *_ = self.game.evaluate_5cards(['9S', '9H', '9D', '9C', '2H'])
		self.assertEqual(res, 7)

		res, *_ = self.game.evaluate_5cards(['8S', '8H', '8D', '7C', '7H'])
		self.assertEqual(res, 6)

		res, *_ = self.game.evaluate_5cards(['2C', '5C', '7C', 'JC', 'QC'])
		self.assertEqual(res, 5)

		res, *_ = self.game.evaluate_5cards(['2H', '3C', '4D', '5S', '6H'])
		self.assertEqual(res, 4)
		res_low_straight, *_ = self.game.evaluate_5cards(['AH', '2C', '3D', '4S', '5H'])
		self.assertEqual(res_low_straight, 4)

		res, *_ = self.game.evaluate_5cards(['7S', '7H', '7D', '2C', '3H'])
		self.assertEqual(res, 3)

		res, *_ = self.game.evaluate_5cards(['JS', 'JH', '9D', '9C', '2H'])
		self.assertEqual(res, 2)

		res, *_ = self.game.evaluate_5cards(['10S', '10H', '2D', '5C', '7H'])
		self.assertEqual(res, 1)

		res, *_ = self.game.evaluate_5cards(['2S', '4H', '8D', 'JC', 'AH'])
		self.assertEqual(res, 0)

	def test_remove_player(self):
		p_indx = next(i for i, (pid, _, _) in enumerate(self.game.players) if pid == self.p3)

		self.game.game_state["blind_player"] = p_indx
		self.game.game_state["current_turn"] = p_indx
		self.game.remove_player(self.p1)

		p_next_indx = next(i for i, (pid, _, _) in enumerate(self.game.players) if pid == self.p3)

		self.assertEqual(self.game.game_state["blind_player"], p_next_indx)
		self.assertEqual(self.game.game_state["current_turn"], p_next_indx)

		self.game.remove_player(self.p3)

		self.assertIsNone(self.game.game_state["current_turn"])
		self.assertEqual(self.game.game_state["blind_player"], 0)

	def test_parse_card_exceptions(self):
		self.assertEqual(self.game.parse_card("Ace of Spades"), (14, "S"))

		with self.assertRaises(ValueError):
			self.game.parse_card("1 of Spades")

		with self.assertRaises(ValueError):
			self.game.parse_card("Ace of Ace")

		with self.assertRaises(ValueError):
			self.game.parse_card("asdasdasd123&")

	def test_showdown_split_pot(self):
		self.game.game_state["pot"] = 100
		self.game.game_state["chips"][self.p1] = 500
		self.game.game_state["chips"][self.p2] = 500
		self.game.game_state["folded_players"] = {self.p3}

		self.game.game_state["community_cards"] = ['AS', 'AH', '2C', '3D', '4S']
		self.game.game_state["hands"][self.p1] = ['9C', '10C']
		self.game.game_state["hands"][self.p2] = ['9D', '10D']

		self.game.showdown_locked()

		self.assertEqual(self.game.game_state["chips"][self.p1], 550)
		self.assertEqual(self.game.game_state["chips"][self.p2], 540)

	def test_one_winner(self):
		self.game.game_state["pot"] = 100
		self.game.game_state["chips"][self.p1] = 500
		self.game.game_state["chips"][self.p2] = 500
		self.game.game_state["folded_players"] = {self.p3}

		msg = {
		 "type": "MOVE",
		 "player_id": self.p2,
		 "data": {"action": "FOLD"}
		}
		self.game.handle_message(msg)

		self.assertEqual(self.game.game_state["chips"][self.p1], 600)

	def test_phase_transition(self):
		self.game.game_state["deck"] = DeckSimple(1)
		self.game.game_state["community_cards"] = []
		self.game.game_state["game_started"] = True

		self.game.game_state["phase"] = "preflop"
		self.game.game_state["current_bet"] = 20

		for p in [self.p1, self.p2, self.p3]:
			self.game.game_state["chips"][p] = 500
			self.game.game_state["round_bets"][p] = 0

		self.game.game_state["players_acted"] = set()

		self.game.game_state["current_turn"] = 0

		for p_id in [self.p1, self.p2, self.p3]:
			msg = {
			 "type": "MOVE",
			 "player_id": p_id,
			 "data": {"action": "CALL"}
			}
			self.game.handle_message(msg)

		self.assertEqual(self.game.game_state["phase"], "flop")
		self.assertEqual(len(self.game.game_state["community_cards"]), 3)

if __name__ == "__main__":
	unittest.main()