import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from card_simple import CardSimple
from deck_simple import DeckSimple
from makao import MakaoGame
from poker import PokerGame
from stats_manager import StatsManager


def create_msg(*args, **kwargs):
    if args:
        kwargs["args"] = args
    return kwargs


class TestPokerWhiteBox(unittest.TestCase):
    def setUp(self):
        self.sent_messages = []
        self.game = PokerGame(
            send_json=lambda conn, msg: self.sent_messages.append((conn, msg)),
            create_msg=create_msg,
        )
        self.p1 = self.game.add_player(MagicMock(name="conn1"), "addr1")
        self.p2 = self.game.add_player(MagicMock(name="conn2"), "addr2")
        self.p3 = self.game.add_player(MagicMock(name="conn3"), "addr3")

    def test_parse_card_accepts_text_short_and_unicode_formats(self):
        self.assertEqual(self.game.parse_card("ace of spades"), (14, "S"))
        self.assertEqual(self.game.parse_card("10H"), (10, "H"))
        self.assertEqual(self.game.parse_card("Q♦"), (12, "D"))

    def test_is_straight_detects_ace_low_and_rejects_duplicates(self):
        self.assertEqual(self.game.is_straight([14, 5, 4, 3, 2]), (True, 5))
        self.assertEqual(self.game.is_straight([14, 14, 13, 12, 11]), (False, None))

    def test_get_next_active_turn_skips_folded_and_all_in_players(self):
        self.game.game_state["folded_players"] = {self.p2}
        self.game.game_state["chips"][self.p3] = 0

        next_turn = self.game.get_next_active_turn(start_index=0)

        self.assertEqual(next_turn, 0)

    def test_betting_round_is_over_when_remaining_players_are_all_in(self):
        self.game.game_state["folded_players"] = {self.p3}
        self.game.game_state["chips"][self.p1] = 0
        self.game.game_state["chips"][self.p2] = 0
        self.game.game_state["players_acted"] = set()
        self.game.game_state["round_bets"] = {self.p1: 50, self.p2: 50}
        self.game.game_state["current_bet"] = 50

        self.assertTrue(self.game.is_betting_round_over())


class TestMakaoWhiteBox(unittest.TestCase):
    def setUp(self):
        self.sent_messages = []
        self.game = MakaoGame(
            send_json=lambda conn, msg: self.sent_messages.append((conn, msg)),
            create_msg=create_msg,
        )
        self.game.players = [
            (1, MagicMock(name="conn1"), "addr1", False, None),
            (2, MagicMock(name="conn2"), "addr2", False, None),
            (3, MagicMock(name="conn3"), "addr3", False, None),
        ]
        self.game.game_state["deck"] = DeckSimple(1)
        self.game.game_state["hands"] = {1: [], 2: [], 3: []}
        self.game.game_state["blocked"] = {1: 0, 2: 0, 3: 0}
        self.game.game_state["drawn"] = []
        self.game.game_state["played"] = []
        self.game.game_state["table"] = [CardSimple("H", "7")]
        self.game.game_state["effect"] = {}
        self.game.game_state["current_turn"] = 1
        self.game.game_state["next_turn"] = 2
        self.game.game_state["makao_called"] = {1: False, 2: False, 3: False}

    def test_draw_effect_accumulates_for_2_3_and_black_king(self):
        self.game.add_effect(CardSimple("H", "2"))
        self.game.add_effect(CardSimple("S", "3"))
        self.game.add_effect(CardSimple("S", "K"))

        self.assertEqual(self.game.game_state["effect"], {"name": "DRAW", "severity": 10})

    def test_club_or_diamond_king_clears_active_effect(self):
        self.game.game_state["effect"] = {"name": "DRAW", "severity": 5}

        self.game.add_effect(CardSimple("C", "K"))

        self.assertEqual(self.game.game_state["effect"], {})

    def test_after_drawing_only_drawn_matching_card_can_be_played(self):
        drawn_matching = CardSimple("D", "7")
        drawn_not_matching = CardSimple("S", "8")
        not_drawn_matching = CardSimple("H", "9")
        self.game.game_state["drawn"] = [drawn_matching, drawn_not_matching]
        self.game.game_state["table"] = [CardSimple("H", "7")]
        self.game.game_state["effect"] = {}

        self.assertTrue(self.game.check_card_eligibility(drawn_matching))
        self.assertFalse(self.game.check_card_eligibility(drawn_not_matching))
        self.assertFalse(self.game.check_card_eligibility(not_drawn_matching))

    def test_resolve_block_effect_adds_block_counter_and_clears_effect(self):
        self.game.game_state["effect"] = {"name": "BLOCK", "severity": 2}
        self.game.game_state["blocked"][1] = 0

        self.game.resolve_effect()

        self.assertEqual(self.game.game_state["blocked"][1], 2)
        self.assertEqual(self.game.game_state["effect"], {})


class TestStatsManagerWhiteBox(unittest.TestCase):
    def test_update_after_game_changes_counters_and_persists_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_file = Path(tmpdir) / "stats.txt"
            history_file = Path(tmpdir) / "history.txt"

            manager = StatsManager(stats_file=str(stats_file), history_file=str(history_file))
            manager.update_after_game(game_type="poker", chips_delta=120, won=True)
            manager.update_after_game(game_type="makao", chips_delta=-20, won=False)

            self.assertEqual(manager.stats["GAMES_PLAYED"], 2)
            self.assertEqual(manager.stats["CHIPS_RESULT"], 100)
            self.assertEqual(manager.stats["POKER_GAMES"], 1)
            self.assertEqual(manager.stats["POKER_HANDS_WON"], 1)
            self.assertEqual(manager.stats["MAKAO_GAMES"], 1)
            self.assertEqual(manager.stats["MAKAO_LOSES"], 1)

            saved_stats = stats_file.read_text(encoding="utf-8")
            saved_history = history_file.read_text(encoding="utf-8")
            self.assertIn("GAMES_PLAYED: 2", saved_stats)
            self.assertIn("CHIPS_RESULT: 100", saved_stats)
            self.assertIn("Poker Win", saved_history)
            self.assertIn("Makao Loss", saved_history)


if __name__ == "__main__":
    unittest.main(verbosity=2)
