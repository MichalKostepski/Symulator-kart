"""Headless regression tests for shared models and network message framing."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from card_simple import CardSimple
from deck_simple import DeckSimple
from host_gui import create_msg, recv_exact, send_json
from makao import MakaoGame
from makao_bot import MakaoBot
from poker import PokerGame
from poker_bot import PokerBot
from stats_manager import StatsManager


class StubSocket:
    def __init__(self, chunks=()):
        self.sent = []
        self.chunks = list(chunks)

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk


class CardAndDeckTests(unittest.TestCase):
    def test_card_identity_and_hashing(self):
        first = CardSimple("H", "A")
        same = CardSimple("H", "A")
        other = CardSimple("S", "A")
        self.assertEqual(first, same)
        self.assertNotEqual(first, other)
        self.assertEqual(len({first, same, other}), 2)
        self.assertEqual(str(first), "AH")

    def test_complete_deck_has_52_unique_cards(self):
        deck = DeckSimple()
        self.assertEqual(len(deck), 52)
        self.assertEqual(len(set(deck.cards)), 52)
        self.assertFalse(deck.is_empty())

    def test_empty_deck_and_restock(self):
        deck = DeckSimple()
        deck.cards.clear()
        self.assertIsNone(deck.draw())
        self.assertTrue(deck.is_empty())
        deck.add_cards([CardSimple("S", "2"), CardSimple("H", "3")])
        self.assertEqual(deck.size(), 2)
        self.assertEqual(str(deck.draw()), "3H")


class WireProtocolTests(unittest.TestCase):
    def test_length_prefixed_json_round_trip(self):
        sock = StubSocket()
        message = create_msg("POKER", "MOVE", player_id=7, data={"action": "CALL"})
        send_json(sock, message)
        self.assertEqual(len(sock.sent), 2)
        self.assertEqual(len(sock.sent[0]), 64)
        self.assertEqual(int(sock.sent[0].strip()), len(sock.sent[1]))
        self.assertEqual(json.loads(sock.sent[1].decode("utf-8")), message)

    def test_recv_exact_handles_fragmentation_and_disconnect(self):
        sock = StubSocket([b"a", b"bc", b"def"])
        self.assertEqual(recv_exact(sock, 5), b"abcde")
        self.assertEqual(recv_exact(sock, 1), b"f")
        self.assertIsNone(recv_exact(sock, 1))


class StorageTests(unittest.TestCase):
    def test_local_stats_survive_reopening(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats = str(Path(tmp) / "stats.txt")
            history = str(Path(tmp) / "history.txt")
            first = StatsManager(stats_file=stats, history_file=history)
            first.update_after_game("poker", chips_delta=15, won=True)
            second = StatsManager(stats_file=stats, history_file=history)
            self.assertEqual(second.stats["GAMES_PLAYED"], 1)
            self.assertEqual(second.stats["CHIPS_RESULT"], 15)
            self.assertEqual(second.stats["POKER_HANDS_WON"], 1)
            self.assertIn("Poker Win", "".join(second.load_history()))


class BotRegressionTests(unittest.TestCase):
    def test_empty_makao_bot_hand_is_no_op(self):
        game = MakaoGame(lambda *args: None, lambda **kw: kw)
        game.players = [(1, None, None, True, MakaoBot(game, 1))]
        game.game_state["hands"] = {1: []}
        game.run_bot(1)

    def test_poker_unknown_deck_excludes_known_cards(self):
        game = PokerGame(lambda *args: None, lambda **kw: kw)
        bot = PokerBot(game, player_id=1, simulations=1)
        cards = bot.build_unknown_deck(["AH", "2C"], ["KD"])
        self.assertEqual(len(cards), 49)
        self.assertNotIn("ace of hearts", cards)
        self.assertNotIn("2 of clubs", cards)
        self.assertNotIn("king of diamonds", cards)


if __name__ == "__main__":
    unittest.main()
