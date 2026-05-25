from itertools import combinations
from deck import Deck
from game import Game



class PokerGame(Game):
    @property
    def name(self):
        return "POKER"

    def __init__(self, send_json, create_msg):

        super().__init__(send_json, create_msg)
        self.STARTING_CHIPS = 500

        self.game_state = {
            "deck": None,
            "hands": {},
            "chips": {},
            "community_cards": [],
            "pot": 0,
            "current_bet": 0,
            "phase": "waiting",
            "blind_amount": 10,
            "blind_player": 0,      # index w liście self.players
            "current_turn": None,   # index w liście self.players
            "round_bets": {},
            "folded_players": set(),
            "players_acted": set(),
            "game_started": False,
        }

    # =========================
    # Player management
    # =========================

    def add_player(self, conn, addr):
        with self.lock:
            player_id = self.next_player_id
            self.next_player_id += 1
            self.players.append((player_id, conn, addr))
            self.game_state["chips"][player_id] = self.STARTING_CHIPS
            return player_id

    def remove_player(self, player_id):
        with self.lock:
            old_len = len(self.players)
            old_blind = self.game_state["blind_player"]
            old_turn = self.game_state["current_turn"]

            remove_index = None
            for i, (pid, _, _) in enumerate(self.players):
                if pid == player_id:
                    remove_index = i
                    break

            self.players = [p for p in self.players if p[0] != player_id]

            self.game_state["hands"].pop(player_id, None)
            self.game_state["chips"].pop(player_id, None)
            self.game_state["round_bets"].pop(player_id, None)
            self.game_state["folded_players"].discard(player_id)
            self.game_state["players_acted"].discard(player_id)

            if not self.players:
                self.game_state["game_started"] = False
                self.game_state["phase"] = "waiting"
                self.game_state["blind_player"] = 0
                self.game_state["current_turn"] = None
                return

            if remove_index is not None:
                if old_len > 0 and old_blind >= old_len:
                    old_blind = 0
                if old_len > 0 and old_turn is not None and old_turn >= old_len:
                    old_turn = 0

                if remove_index < old_blind:
                    old_blind -= 1
                elif remove_index == old_blind and old_blind >= len(self.players):
                    old_blind = 0

                if old_turn is not None:
                    if remove_index < old_turn:
                        old_turn -= 1
                    elif remove_index == old_turn:
                        old_turn = None

            self.game_state["blind_player"] = max(0, min(old_blind, len(self.players) - 1))
            self.game_state["current_turn"] = old_turn

            if len(self.players) < 2:
                self.game_state["game_started"] = False
                self.game_state["phase"] = "waiting"
                self.game_state["current_turn"] = None
                print("[INFO] Za mało graczy, gra zatrzymana")
                self.send_table_update()

    def print_players(self):
        with self.lock:
            print("=== PLAYERS ===")
            for pid, _, addr in self.players:
                print(f"Gracz {pid} | {addr}")

    def print_state(self):
        with self.lock:
            print("=== GAME STATE ===")
            for key, value in self.game_state.items():
                print(f"{key}: {value}")

    # =========================
    # Messaging
    # =========================

    def send_to_player(self, conn, msg):
        self.send_json(conn, msg)

    def broadcast(self, msg):
        disconnected = []

        for player_id, conn, _ in list(self.players):
            try:
                self.send_to_player(conn, msg)
            except Exception as e:
                print(f"[ERROR] Nie udało się wysłać do gracza {player_id}: {e}")
                disconnected.append(player_id)

        for pid in disconnected:
            self.remove_player(pid)

    # =========================
    # Helpers
    # =========================

    def get_active_player_ids(self):
        return [
            player_id for player_id, _, _ in self.players
            if player_id not in self.game_state["folded_players"]
        ]

    def get_next_active_turn(self, start_index):
        if not self.players:
            return None

        next_index = start_index
        checked = 0

        while checked < len(self.players):
            next_index = (next_index + 1) % len(self.players)
            next_player_id = self.players[next_index][0]

            if next_player_id not in self.game_state["folded_players"]:
                return next_index

            checked += 1

        return None

    def reset_betting_round(self):
        self.game_state["current_bet"] = 0
        self.game_state["players_acted"] = set()

        for player_id, _, _ in self.players:
            if player_id not in self.game_state["folded_players"]:
                self.game_state["round_bets"][player_id] = 0

    def send_turn_to_current_player(self):
        turn_index = self.game_state["current_turn"]
        if turn_index is None or turn_index >= len(self.players):
            return

        turn_player_id, turn_conn, _ = self.players[turn_index]

        turn_msg = self.create_msg(
            game="POKER",
            msg_type="TURN",
            player_id=turn_player_id,
            data={
                "current_bet": self.game_state["current_bet"],
                "pot": self.game_state["pot"],
                "phase": self.game_state["phase"],
                "community_cards": [str(card) for card in self.game_state["community_cards"]],
                "your_bet": self.game_state["round_bets"].get(turn_player_id, 0)
            }
        )

        self.send_to_player(turn_conn, turn_msg)
        print(f"[TURN] Tura gracza {turn_player_id}")

    def send_table_update(self):
        msg = self.create_msg(
            game="POKER",
            msg_type="TABLE",
            data={
                "phase": self.game_state["phase"],
                "pot": self.game_state["pot"],
                "current_bet": self.game_state["current_bet"],
                "community_cards": [str(card) for card in self.game_state["community_cards"]],
                "folded_players": list(self.game_state["folded_players"]),
                "chips": self.game_state["chips"]
            }
        )
        self.broadcast(msg)

    def is_betting_round_over(self):
        active_players = self.get_active_player_ids()

        if len(active_players) <= 1:
            return True

        for pid in active_players:
            if pid not in self.game_state["players_acted"]:
                return False

        for pid in active_players:
            if self.game_state["round_bets"].get(pid, 0) != self.game_state["current_bet"]:
                return False

        return True

    # =========================
    # Card evaluation
    # =========================

    def parse_card(self, card):
        card_str = str(card).strip().lower()

        if " of " in card_str:
            rank_str, suit_str = card_str.split(" of ")

            rank_map_text = {
                "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                "8": 8, "9": 9, "10": 10,
                "jack": 11, "queen": 12, "king": 13, "ace": 14
            }

            suit_map_text = {
                "spades": "S",
                "hearts": "H",
                "diamonds": "D",
                "clubs": "C"
            }

            if rank_str not in rank_map_text or suit_str not in suit_map_text:
                raise ValueError(f"Nieznany format karty: {card}")

            return (rank_map_text[rank_str], suit_map_text[suit_str])

        card_str = card_str.upper()
        card_str = card_str.replace("♠", "S")
        card_str = card_str.replace("♥", "H")
        card_str = card_str.replace("♦", "D")
        card_str = card_str.replace("♣", "C")

        suit = card_str[-1]
        rank = card_str[:-1]

        rank_map_short = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
            "8": 8, "9": 9, "10": 10, "T": 10,
            "J": 11, "Q": 12, "K": 13, "A": 14
        }

        if rank not in rank_map_short:
            raise ValueError(f"Nieznany format karty: {card}")

        return (rank_map_short[rank], suit)

    def is_straight(self, values):
        unique_values = sorted(set(values), reverse=True)

        if len(unique_values) != 5:
            return (False, None)

        if unique_values[0] - unique_values[4] == 4:
            return (True, unique_values[0])

        if unique_values == [14, 5, 4, 3, 2]:
            return (True, 5)

        return (False, None)

    def evaluate_5cards(self, cards5):
        parsed = [self.parse_card(card) for card in cards5]
        values = sorted([v for v, s in parsed], reverse=True)
        suits = [s for v, s in parsed]

        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1

        count_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))

        is_flush = len(set(suits)) == 1
        straight, straight_high = self.is_straight(values)

        if is_flush and straight:
            return (8, straight_high)

        if count_items[0][1] == 4:
            four_value = count_items[0][0]
            kicker = count_items[1][0]
            return (7, four_value, kicker)

        if count_items[0][1] == 3 and count_items[1][1] == 2:
            three_value = count_items[0][0]
            pair_value = count_items[1][0]
            return (6, three_value, pair_value)

        if is_flush:
            return (5, *values)

        if straight:
            return (4, straight_high)

        if count_items[0][1] == 3:
            three_value = count_items[0][0]
            kickers = sorted([v for v in values if v != three_value], reverse=True)
            return (3, three_value, *kickers)

        if count_items[0][1] == 2 and count_items[1][1] == 2:
            pair1 = max(count_items[0][0], count_items[1][0])
            pair2 = min(count_items[0][0], count_items[1][0])
            kicker = [v for v in values if v != pair1 and v != pair2][0]
            return (2, pair1, pair2, kicker)

        if count_items[0][1] == 2:
            pair_value = count_items[0][0]
            kickers = sorted([v for v in values if v != pair_value], reverse=True)
            return (1, pair_value, *kickers)

        return (0, *values)

    def get_best_hand(self, cards7):
        best_score = None
        best_combo = None

        for combo in combinations(cards7, 5):
            score = self.evaluate_5cards(combo)
            if best_score is None or score > best_score:
                best_score = score
                best_combo = combo

        return best_score, best_combo

    def hand_name(self, score):
        category = score[0]
        names = {
            8: "Straight Flush",
            7: "Kareta",
            6: "Full House",
            5: "Kolor",
            4: "Strit",
            3: "Trójka",
            2: "Dwie Pary",
            1: "Jedna Para",
            0: "Wysoka Karta"
        }
        return names.get(category, "Nieznany układ")

    # =========================
    # Game flow
    # =========================

    def start_game(self):
        with self.lock:
            if self.game_state["game_started"]:
                print("[INFO] Gra już została rozpoczęta")
                return

            if len(self.players) < 2:
                print("[INFO] Za mało graczy, minimum 2")
                return

            self.game_state["game_started"] = True
            print("[INFO] Start gry (POKER)")
            self.start_round_locked()

    def start_round_locked(self):
        if len(self.players) < 2:
            self.game_state["game_started"] = False
            self.game_state["phase"] = "waiting"
            self.game_state["current_turn"] = None
            print("[INFO] Za mało graczy, nie można rozpocząć rundy")
            return

        deck = Deck()
        deck.shuffle()

        print("=== START RUNDY ===")

        self.game_state["deck"] = deck
        self.game_state["hands"] = {}
        self.game_state["community_cards"] = []
        self.game_state["pot"] = 0
        self.game_state["current_bet"] = 0
        self.game_state["phase"] = "preflop"
        self.game_state["round_bets"] = {}
        self.game_state["folded_players"] = set()
        self.game_state["players_acted"] = set()

        if self.game_state["blind_player"] >= len(self.players):
            self.game_state["blind_player"] = 0

        blind_index = self.game_state["blind_player"]

        for player_id, conn, _ in self.players:
            hand = [deck.draw(), deck.draw()]
            self.game_state["hands"][player_id] = hand
            self.game_state["round_bets"][player_id] = 0

            msg = self.create_msg(
                game="POKER",
                msg_type="HAND",
                player_id=player_id,
                data={"cards": [str(card) for card in hand]}
            )
            self.send_to_player(conn, msg)

        blind_player_id, _, _ = self.players[blind_index]
        available_chips = self.game_state["chips"][blind_player_id]
        actual_blind = min(self.game_state["blind_amount"], available_chips)

        self.game_state["chips"][blind_player_id] -= actual_blind
        self.game_state["round_bets"][blind_player_id] = actual_blind
        self.game_state["pot"] = actual_blind
        self.game_state["current_bet"] = actual_blind

        print(f"[BLIND] Gracz {blind_player_id} wpłaca blind: {actual_blind}")

        self.game_state["current_turn"] = self.get_next_active_turn(blind_index)

        self.send_table_update()
        self.send_turn_to_current_player()

    def award_pot_to_winner_locked(self, winner_id, reason="WIN"):
        self.game_state["chips"][winner_id] += self.game_state["pot"]

        msg = self.create_msg(
            game="POKER",
            msg_type="WINNER",
            player_id=winner_id,
            data={
                "winner": winner_id,
                "pot": self.game_state["pot"],
                "reason": reason,
                "community_cards": [str(card) for card in self.game_state["community_cards"]],
            }
        )
        self.broadcast(msg)

        print(f"[WINNER] Gracz {winner_id} wygrywa pulę {self.game_state['pot']} ({reason})")

        current_blind_idx = self.game_state["blind_player"]
        next_blind_candidate_id = self.players[(current_blind_idx + 1) % len(self.players)][0]

        self.handle_bancruptcies()

        if len(self.players) >= 2:
            new_idx = 0
            for i, p in enumerate(self.players):
                if p[0] == next_blind_candidate_id:
                    new_idx = i
                    break
            
            self.game_state["blind_player"] = new_idx
            self.start_round_locked()
        else:
            self.game_state["game_started"] = False
            self.game_state["phase"] = "waiting"
            self.game_state["current_turn"] = None

    def showdown_locked(self):
        active_players = self.get_active_player_ids()
        results = []

        for pid in active_players:
            cards7 = self.game_state["hands"][pid] + self.game_state["community_cards"]
            best_score, best_combo = self.get_best_hand(cards7)

            results.append({
                "player_id": pid,
                "score": best_score,
                "best_combo": [str(card) for card in best_combo],
                "hand_name": self.hand_name(best_score)
            })

            print(f"[SHOWDOWN] Gracz {pid}")
            print(f"  7 kart: {[str(c) for c in cards7]}")
            print(f"  najlepszy układ: {results[-1]['hand_name']}")
            print(f"  best combo: {results[-1]['best_combo']}")
            print(f"  score: {best_score}")

        best_score_overall = max(r["score"] for r in results)
        winners = [r for r in results if r["score"] == best_score_overall]

        if len(winners) == 1:
            winner = winners[0]
            self.game_state["chips"][winner["player_id"]] += self.game_state["pot"]
            msg = self.create_msg(
                game="POKER",
                msg_type="WINNER",
                player_id=winner["player_id"],
                data={
                    "winner": winner["player_id"],
                    "pot": self.game_state["pot"],
                    "reason": "SHOWDOWN",
                    "community_cards": [str(card) for card in self.game_state["community_cards"]],
                    "hand_name": winner["hand_name"],
                    "best_combo": winner["best_combo"]
                }
            )
            self.broadcast(msg)
            print(f"[WINNER] Gracz {winner['player_id']} wygrywa pulę {self.game_state['pot']}")
            print(f"[WINNER] Układ: {winner['hand_name']}")

        else:
            winner_ids = [w["player_id"] for w in winners]
            split_pot = self.game_state["pot"] // len(winners)
            for wid in winner_ids:
                self.game_state["chips"][wid] += split_pot

            msg = self.create_msg(
                game="POKER",
                msg_type="WINNER",
                data={
                    "winner": winner_ids,
                    "pot": self.game_state["pot"],
                    "reason": "SHOWDOWN_TIE",
                    "community_cards": [str(card) for card in self.game_state["community_cards"]],
                    "hand_name": winners[0]["hand_name"],
                    "best_combo": [w["best_combo"] for w in winners]
                }
            )
            self.broadcast(msg)
            print(f"[WINNER] Remis między graczami: {winner_ids}")
            print(f"[WINNER] Najlepszy układ: {winners[0]['hand_name']}")

        current_blind_idx = self.game_state["blind_player"]
        next_blind_candidate_id = self.players[(current_blind_idx + 1) % len(self.players)][0]

        self.handle_bancruptcies()

        if len(self.players) >= 2:
            new_idx = 0
            for i, p in enumerate(self.players):
                if p[0] == next_blind_candidate_id:
                    new_idx = i
                    break
            
            self.game_state["blind_player"] = new_idx
            self.start_round_locked()
        else:
            self.game_state["game_started"] = False
            self.game_state["phase"] = "waiting"
            self.game_state["current_turn"] = None

    def advance_phase_locked(self):
        deck = self.game_state["deck"]

        if self.game_state["phase"] == "preflop":
            self.game_state["phase"] = "flop"
            self.game_state["community_cards"] = [deck.draw(), deck.draw(), deck.draw()]
            print(f"[PHASE] FLOP: {self.game_state['community_cards']}")

        elif self.game_state["phase"] == "flop":
            self.game_state["phase"] = "turn"
            self.game_state["community_cards"].append(deck.draw())
            print(f"[PHASE] TURN: {self.game_state['community_cards']}")

        elif self.game_state["phase"] == "turn":
            self.game_state["phase"] = "river"
            self.game_state["community_cards"].append(deck.draw())
            print(f"[PHASE] RIVER: {self.game_state['community_cards']}")

        elif self.game_state["phase"] == "river":
            self.game_state["phase"] = "showdown"
            print("[PHASE] SHOWDOWN")
            self.send_table_update()
            self.showdown_locked()
            return

        self.reset_betting_round()

        start_index = self.game_state["blind_player"]
        self.game_state["current_turn"] = self.get_next_active_turn(start_index)

        self.send_table_update()
        self.send_turn_to_current_player()

    # =========================
    # Incoming messages
    # =========================

    def handle_message(self, msg):
        with self.lock:
            msg_type = msg.get("type")
            player_id = msg.get("player_id")
            data = msg.get("data", {})

            #==================
            # CHAT
            #==================

            if msg_type == "CHAT":
                chat_text = msg.get("chat")
                broadcast_msg = self.create_msg (
                    game=msg.get("game"),
                    msg_type="CHAT",
                    player_id=player_id,
                    data=data,
                    chat=chat_text
                    )
                self.broadcast(broadcast_msg)
                return


            #===============
            # GAME
            #===============

            if msg_type != "MOVE":
                return

            if not self.game_state["game_started"]:
                print("[INFO] Ignoruję ruch, gra nie została rozpoczęta")
                return

            if self.game_state["current_turn"] is None:
                print("[ERROR] Brak aktualnej tury")
                return

            if self.game_state["current_turn"] >= len(self.players):
                print("[ERROR] current_turn poza zakresem")
                return

            action = data.get("action")
            print(f"[MOVE] Gracz {player_id} wykonał ruch: {action}")

            current_turn_player_id = self.players[self.game_state["current_turn"]][0]

            if player_id != current_turn_player_id:
                print(f"[ERROR] To nie tura gracza {player_id}")
                return

            if player_id in self.game_state["folded_players"]:
                print(f"[ERROR] Gracz {player_id} już spasował")
                return

            if action == "CALL":
                amount_to_call = self.game_state["current_bet"] - self.game_state["round_bets"].get(player_id, 0)
                if amount_to_call < 0:
                    amount_to_call = 0

                available_chips = self.game_state["chips"][player_id]
                actual_call = min(amount_to_call, available_chips)

                self.game_state["chips"][player_id] -= actual_call
                self.game_state["round_bets"][player_id] = self.game_state["round_bets"].get(player_id, 0) + actual_call
                self.game_state["pot"] += actual_call
                self.game_state["players_acted"].add(player_id)

                print(f"[CALL] Gracz {player_id} dopłaca: {amount_to_call}")
                print(f"[POT] Nowa pula: {self.game_state['pot']}")

            elif action == "FOLD":
                self.game_state["folded_players"].add(player_id)
                self.game_state["players_acted"].add(player_id)
                print(f"[FOLD] Gracz {player_id} spasował")

            elif action == "RAISE":
                amount = data.get("amount")

                if amount is None:
                    print(f"[ERROR] Brak kwoty raise od gracza {player_id}")
                    return

                try:
                    new_bet = int(amount)
                except ValueError:
                    print(f"[ERROR] Nieprawidłowa kwota raise: {amount}")
                    return

                if new_bet <= self.game_state["current_bet"]:
                    print("[ERROR] Raise musi być większy niż current_bet")
                    self.send_turn_to_current_player()
                    return

                amount_to_add = new_bet - self.game_state["round_bets"].get(player_id, 0)
                available_chips = self.game_state["chips"][player_id]
                
                if amount_to_add > available_chips:
                    print(f"[ERROR] Gracz {player_id} nie ma tylu żetonów na raise!")
                    self.send_turn_to_current_player()
                    return

                if amount_to_add < 0:
                    print("[ERROR] Nieprawidłowy raise")
                    self.send_turn_to_current_player()
                    return

                self.game_state["chips"][player_id] -= amount_to_add
                self.game_state["round_bets"][player_id] = new_bet
                self.game_state["current_bet"] = new_bet
                self.game_state["pot"] += amount_to_add

                self.game_state["players_acted"] = {player_id}

                print(f"[RAISE] Gracz {player_id} podbija do: {new_bet}")
                print(f"[POT] Nowa pula: {self.game_state['pot']}")
                print(f"[BET] Nowy current_bet: {self.game_state['current_bet']}")

            else:
                print(f"[ERROR] Nieznana akcja: {action}")
                return

            self.send_table_update()

            active_players = self.get_active_player_ids()

            if len(active_players) == 1:
                winner = active_players[0]
                self.award_pot_to_winner_locked(winner, reason="ALL_FOLDED")
                return

            if self.is_betting_round_over():
                print("[INFO] Koniec rundy licytacji")
                self.advance_phase_locked()
                return

            next_turn = self.get_next_active_turn(self.game_state["current_turn"])
            self.game_state["current_turn"] = next_turn
            self.send_turn_to_current_player()

    def handle_bancruptcies(self):
        bankrupts = [pid for pid, chips in self.game_state["chips"].items() if chips <= 0]
        for pid in bankrupts:
            print(f"[DEFEAT] Gracz {pid} stracił wszystkie żetony.")
            for p_id, conn, _ in list(self.players):
                if p_id == pid:
                    msg = self.create_msg("POKER", "DEFEAT", player_id=pid)
                    try:
                        self.send_to_player(conn, msg)
                    except:
                        pass
                    self.remove_player(pid)

                if pid in self.game_state["chips"]:
                    del self.game_state["chips"][pid]
