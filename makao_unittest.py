from makao import MakaoGame
from card_simple import CardSimple
from deck_simple import DeckSimple

import unittest
from unittest.mock import MagicMock

class TestMakao(unittest.TestCase):
	def setUp(self):
		self.mock_send = MagicMock()
		self.mock_create_msg = MagicMock(side_effect=lambda **kwargs: kwargs)
		
		self.game = MakaoGame(self.mock_send, self.mock_create_msg)
		self.game.players = [
			(1, MagicMock(), "addr1"),
			(2, MagicMock(), "addr2"),
			(3, MagicMock(), "addr3")
		]
		
		from deck_simple import DeckSimple
		self.game.game_state["deck"] = DeckSimple(1)
		self.game.game_state["hands"] = {1: [], 2: [], 3: []}
		self.game.game_state["blocked"] = {1: 0, 2: 0, 3: 0}
		self.game.game_state["drawn"] = []
		self.game.game_state["played"] = []
		self.game.game_state["table"] = [CardSimple('H', '10')]
		self.game.game_state["effect"] = {}

	def test_card_eligibility_basic(self):
		self.game.game_state["table"] = [CardSimple('H', '7')]
		self.game.game_state["effect"] = {}

		self.assertTrue(self.game.check_card_eligibility(CardSimple('S', '7')))
		self.assertTrue(self.game.check_card_eligibility(CardSimple('H', '2')))
		self.assertTrue(self.game.check_card_eligibility(CardSimple('H', '9')))
		self.assertTrue(self.game.check_card_eligibility(CardSimple('D', '7')))
		self.assertTrue(self.game.check_card_eligibility(CardSimple('S', 'Q')))

		self.assertFalse(self.game.check_card_eligibility(CardSimple('S', '8')))
		self.assertFalse(self.game.check_card_eligibility(CardSimple('D', 'K')))
		self.assertFalse(self.game.check_card_eligibility(CardSimple('S', '5')))

		self.game

	def test_draw_effect(self):
		self.game.game_state["effect"] = {}

		card2 = CardSimple('H', '2')
		self.game.add_effect(card2)
		self.assertEqual(self.game.game_state["effect"]["name"], "DRAW")
		self.assertEqual(self.game.game_state["effect"]["severity"], 2)

		self.game.add_effect(CardSimple('S', '2'))
		self.assertEqual(self.game.game_state["effect"]["name"], "DRAW")
		self.assertEqual(self.game.game_state["effect"]["severity"], 4)

		self.game.add_effect(CardSimple('H', '3'))
		self.assertEqual(self.game.game_state["effect"]["name"], "DRAW")
		self.assertEqual(self.game.game_state["effect"]["severity"], 7)

		self.game.add_effect(CardSimple('S', 'K'))
		self.assertEqual(self.game.game_state["effect"]["name"], "DRAW")
		self.assertEqual(self.game.game_state["effect"]["severity"], 12)

		card2 = CardSimple('H', '4')
		self.game.game_state["effect"] = {}
		self.game.add_effect(card2)
		self.assertEqual(self.game.game_state["effect"]["name"], "BLOCK")
		self.assertEqual(self.game.game_state["effect"]["severity"], 1)

		self.game.game_state["effect"] = {}
		card2 = CardSimple('H', 'J')
		self.game.add_effect(card2)
		self.assertEqual(self.game.game_state["effect"]["name"], "DEMAND FACE")

		self.game.game_state["effect"] = {}
		card2 = CardSimple('H', 'A')
		self.game.add_effect(card2)
		self.assertEqual(self.game.game_state["effect"]["name"], "DEMAND SUIT")


	def test_skipping_blocked_player(self):
		self.game.game_state["current_turn"] = 1
		self.game.game_state["blocked"] = {1: 0, 2: 1, 3: 0}
		
		self.game.update_next_turn(0)
		
		self.assertEqual(self.game.game_state["next_turn"], 3)
		self.assertEqual(self.game.game_state["blocked"][2], 0)

	def test_get_previous(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 2
		self.game.game_state["next_turn"] = 3
		self.game.game_state["hands"] = {1: [CardSimple('H', 'A')], 2: [CardSimple('S', '4'), CardSimple('S', 'K')], 3: [CardSimple('S', '5')]}
		self.game.game_state["table"] = [CardSimple('D', '7')]  # byle jaka karta
		self.game.game_state["effect"] = {}
		self.game.game_state["played"] = []
		self.game.game_state["drawn"] = []

		msg1 = {
			"type": "PLAY",
			"player_id": 2,
			"data": {"face": "K", "suit": "S"}
		}
		self.game.handle_message(msg1)

		msg2 = {
			"type": "END TURN",
			"player_id": 2,
		}
		self.game.handle_message(msg2)

		self.game.start_round_locked()

		self.assertEqual(self.game.game_state["current_turn"], 1)

	def test_full_play_action(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 1
		self.game.game_state["table"] = [CardSimple('H', '10')]
		self.game.game_state["hands"] = {1: [CardSimple('H', 'A')], 2: [CardSimple('S', '4')], 3: [CardSimple('S', '5')]}
		self.game.game_state["played"] = []
		self.game.game_state["drawn"] = []
		self.game.game_state["effect"] = {}

		msg = {
			"type": "PLAY",
			"player_id": 1,
			"data": {"face": "A", "suit": "H", "suit_demand": "S"}
		}
		self.game.handle_message(msg)

		self.assertEqual(len(self.game.game_state["hands"][1]), 0)
		self.assertEqual(self.game.game_state["table"][-1].face, "A")
		self.assertEqual(self.game.game_state["effect"]["name"], "DEMAND SUIT")
		self.assertEqual(self.game.game_state["game_started"], False) #test check_winner


	def test_cards_played(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 2
		self.game.game_state["table"] = [CardSimple('S', '10')]
		self.game.game_state["hands"] = {1: [CardSimple('H', 'A')], 2: [CardSimple('S', '7'), CardSimple('C', '7')], 3: [CardSimple('S', '5')]}
		self.game.game_state["played"] = []
		self.game.game_state["drawn"] = []
		self.game.game_state["effect"] = {}

		msg1 = {
			"type": "PLAY",
			"player_id": 2,
			"data": {"face": "7", "suit": "S"}
		}
		self.game.handle_message(msg1)

		msg2 = {
			"type": "PLAY",
			"player_id": 2,
			"data": {"face": "7", "suit": "C"}
		}
		self.game.handle_message(msg2)

		self.assertEqual(len(self.game.game_state["played"]), 2)


	def test_draw_action(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 1
		self.game.game_state["hands"][1] = [CardSimple('D', '9')]
		
		initial_hand_size = len(self.game.game_state["hands"][1])
		
		msg = {"type": "DRAW", "player_id": 1}
		self.game.handle_message(msg)
		
		self.assertEqual(len(self.game.game_state["hands"][1]), initial_hand_size + 1)
		self.assertEqual(len(self.game.game_state["drawn"]), 1)

	def test_empty_deck_reshuffle(self):
		self.game.game_state["deck"].cards = [] 
		self.game.game_state["table"] = [CardSimple('S', '5'), CardSimple('H', '6'), CardSimple('D', '7')]
		self.game.game_state["current_turn"] = 1
		self.game.game_state["drawn"] = []
		
		drawn_card = self.game.draw()
		
		self.assertIsNotNone(drawn_card)
		self.assertEqual(len(self.game.game_state["table"]), 1)
		self.assertEqual(str(self.game.game_state["table"][0]), "7D")
		self.assertTrue(len(self.game.game_state["deck"].cards) > 0)

	def test_resolve_draw_effect(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 1
		self.game.game_state["effect"] = {"name": "DRAW", "severity": 5}
		self.game.game_state["hands"][1] = [CardSimple('S', '10')]
		self.game.game_state["next_turn"] = 2
		
		self.game.game_state["table"] = [CardSimple('D', '5')] 

		msg = {"type": "END TURN", "player_id": 1}
		self.game.handle_message(msg)
		
		self.assertEqual(len(self.game.game_state["hands"][1]), 6)
		self.assertEqual(self.game.game_state["effect"], {})

	def test_demand_suit_logic(self):
		self.game.game_state["game_started"] = True
		self.game.game_state["current_turn"] = 2
		self.game.game_state["table"] = [CardSimple('H', 'A')]
		self.game.game_state["effect"] = {"name": "DEMAND SUIT", "suit": "S"}
		
		self.game.game_state["hands"][2] = [CardSimple('H', '10'), CardSimple('S', '7')]
		
		self.assertFalse(self.game.check_card_eligibility(CardSimple('H', '10')))
		
		self.assertTrue(self.game.check_card_eligibility(CardSimple('S', '7')))


if __name__ == "__main__":
	unittest.main()