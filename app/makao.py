from game import Game
from deck_simple import DeckSimple
from card_simple import CardSimple
from makao_bot import MakaoBot


class MakaoGame(Game):

    @property
    def name(self):
        return "MAKAO"

    def __init__(self, send_json, create_msg):
        super().__init__(send_json, create_msg)

        self.settings = {
            "number_of_decks": 1,
            "starting_cards": 3
        }

        self.game_state = {
            "deck": None,
            "game_started": False,
            "table": None,
            "hands": None,
            "blocked": None,
            "current_turn": None,
            "next_turn": None,
            "played": None,
            "effect": None,
            "drawn": None,
            "makao_called": None,
            "winners": None,
        }





    def print_players(self):
        with self.lock:
            print("=== PLAYERS ===")
            for player in self.players:
                pid = player[0]
                addr = player[2] if len(player) >= 3 else None
                print(f"Gracz {pid} | {addr}")

    def print_state(self):
        with self.lock:
            print("=== GAME STATE ===")
            for key, value in self.game_state.items():
                print(f"{key}: {value}")





    def add_bot(self):
        with self.lock:
            player_id = self.next_player_id
            self.next_player_id += 1

            bot = MakaoBot(self, player_id)

            self.players.append((player_id, None, None, True, bot))

            print(f"[MAKAO] Bot {player_id} dołączył")

            return player_id

    def run_bot(self, player_id):
        bot = None

        for player in self.players:
            pid = player[0]
            is_bot = len(player) >= 4 and player[3]
            b = player[4] if len(player) >= 5 else None
            if pid == player_id and is_bot:
                bot = b
                break

        if not bot:
            return

        hand = self.game_state["hands"][player_id]

        print(self.game_state["table"][-1])
        weights = []
        for i in range(len(hand)):
            if self.check_card_eligibility(hand[i]):
                weights.append(20)
            else:
                weights.append(0)
        print(hand)
        print(weights)
        if max(weights) == 0:
            if len(self.game_state["played"]) == 0 and len(self.game_state["drawn"]) == 0 and not self.game_state["effect"].get("name") in ["DRAW", "BLOCK"]:
                msg = self.create_msg(
                    game="MAKAO",
                    msg_type="DRAW",
                    player_id = player_id
                )
            else:
                msg = self.create_msg(
                    game="MAKAO",
                    msg_type="END TURN",
                    player_id = player_id
                )
            print(msg)
            self.handle_message(msg)
            return

        suits = {}
        suits["C"] = 0
        suits["D"] = 0
        suits["H"] = 0
        suits["S"] = 0

        faces = {}
        for i in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']:
            faces[i] = 0

        for i in range(len(hand)):
            card = hand[i]
            suits[card.suit] += 1
            faces[card.face] += 1

        next_turn = self.game_state["next_turn"]
        if next_turn == None:
            next_turn_cards_number = 0
        else:
            next_turn_cards_number = len(self.game_state["hands"][next_turn])

        for i in range(len(hand)):
            card = hand[i]
            if weights[i] == 0:
                continue
            if len(hand) == 1:
                weights[i] += 1000
            if card.face in ["2", "3", "4", "J", "Q", "K", "A"]:
                weights[i] -= 10
            weights[i] += suits[card.suit]
            weights[i] += 3 * faces[card.face]
            if (next_turn_cards_number <= 2):
                if card.face in ["2", "3", "4"]:
                    weights[i] += 30
                elif card.face == "K" and card.suit == "H":
                    weights[i] += 30
                elif card.face == "J":
                    weights[i] += 25
                elif card.face == "A":
                    weights[i] += 15
                elif card.face == "Q":
                    weights[i] -= 100

        best_weight = max(weights)

        if best_weight < 0:
            msg = self.create_msg(
                    game="MAKAO",
                    msg_type="DRAW",
                    player_id = player_id
                )
            self.handle_message(msg)
            return

        best_play_index = weights.index(best_weight)
        best_play = hand[best_play_index]

        face = None
        suit = None

        if best_play.face == "J":
            face = max(faces, key=faces.get)

        if best_play.face == "A":
            suit = max(suits, key=suits.get)

        msg = self.create_msg(
            game = "MAKAO",
            msg_type = "PLAY",
            player_id = player_id,
            data ={
                "face": best_play.face,
                "suit": best_play.suit,
                "face_demand": face,
                "suit_demand": suit,
            }
        )
        print(weights)
        print(msg)
        print("")
        self.handle_message(msg)






    def update_next_turn(self, start_index):
        if not self.players:
            return None

        next_index = start_index
        checked = 0

        while checked < len(self.players):
            next_index = (next_index + 1) % len(self.players)
            next_player_id = self.players[next_index][0]

            if self.game_state["blocked"][next_player_id] == 0:
                self.game_state["next_turn"] = next_player_id
                return
            else:
                self.game_state["blocked"][next_player_id] -= 1
                msg = self.create_msg(
                    game="MAKAO",
                    msg_type="BLOCK",
                    data={
                        "player_id": next_player_id,
                        "duration": self.game_state["blocked"][next_player_id]
                    }
                )
                self.broadcast(msg)

            checked += 1



    def get_previous(self, start_index):
        if not self.players:
            return None

        prev_index = start_index
        checked = 0

        while checked < len(self.players):
            prev_index = (prev_index - 1) % len(self.players)
            prev_player_id = self.players[prev_index][0]

            if self.game_state["blocked"][prev_player_id] == 0:
                return prev_player_id

            checked += 1

        return self.players[start_index][0]

    def get_player_conn(self, player_id):
        for player in self.players:
            pid = player[0]
            conn = player[1]
            if pid == player_id:
                return conn
        return None

    def get_player_index(self, player_id):
        for i, player in enumerate(self.players):
            if player[0] == player_id:
                return i
        return None

    def send_turn_to_current_player(self):

        turn_player_id = self.game_state["current_turn"]

        if turn_player_id is None:
            return

        index = self.get_player_index(turn_player_id)
        if index is not None and len(self.players[index]) >= 4 and self.players[index][3] == True:
            self.run_bot(turn_player_id)
            return

        turn_player_id = self.game_state["current_turn"]
        turn_conn = self.get_player_conn(turn_player_id)

        turn_msg = self.create_msg(
            game="MAKAO",
            msg_type="TURN",
            player_id=turn_player_id,
            data={
                "hand": [str(card) for card in self.game_state["hands"][turn_player_id]],
                "table": str(self.game_state["table"][-1]),
                "played": [str(card) for card in self.game_state["played"]],
                "effect": self.game_state["effect"],
                "drawn": [str(card) for card in self.game_state["drawn"]]
            }
        )

        self.send_to_player(turn_conn, turn_msg)
        print(f"[TURN] Tura gracza {turn_player_id}")

    def send_table_update(self):
        msg = self.create_msg(
            game="MAKAO",
            msg_type="TABLE",
            data={
                "players": [
                {
                    "player_id": pid,
                    "cards_count": len(self.game_state["hands"].get(pid, [])),
                    "blocked": self.game_state["blocked"].get(pid, 0),
                    "makao": self.game_state["makao_called"].get(pid, False)
                }
                for pid in [player[0] for player in self.players]
                ],
                "turn": self.game_state["current_turn"],
                "played": [str(card) for card in self.game_state["played"]],
                "table": str(self.game_state["table"][-1]),
                "effect": self.game_state["effect"]
            }
        )
        self.broadcast(msg)

    def draw(self):
        if len(self.game_state["deck"].cards) > 0:
            card = self.game_state["deck"].draw()
            self.game_state["drawn"].append(card)
            return card
        elif len(self.game_state["table"]) == 1:
            msg = self.create_msg(
                game="MAKAO",
                msg_type="DRAW ERROR",
                data={
                    "player_id": self.game_state["current_turn"]
                }
            )
            self.broadcast(msg)
        else:
            top_card = self.game_state["table"][-1]
            new_deck = DeckSimple(0)
            new_deck.cards = self.game_state["table"][:-1]

            self.game_state["deck"] = new_deck
            self.game_state["table"] = [top_card]

            self.game_state["deck"].shuffle()

            card = self.game_state["deck"].draw()
            self.game_state["drawn"].append(card)
            return card

    def check_winner(self):
        current_player = self.game_state["current_turn"]

        if len(self.game_state["hands"][current_player]) == 0:
            print(f"[INFO] Gracz {current_player} wygrał grę.")

            msg = self.create_msg(
                game="MAKAO",
                msg_type="WINNER",
                data={
                    "winner": current_player
                }
            )

            self.broadcast(msg)

            self.game_state["game_started"] = False
            self.game_state["current_turn"] = None

            return True

        return False





    def check_card_eligibility(self, card):
        top_card = self.game_state["table"][-1]
        if len(self.game_state["played"]) > 0:
            if card.face == self.game_state["played"][0].face:
                return True
            return False
        if top_card.face == 'Q':
            return True
        if self.game_state["effect"].get("name") == "DRAW":
            if top_card.face == 'K':
                if card.face == 'Q' and card.suit == top_card.suit:
                    return True
                return False
            else:
                if (card.face == top_card.face or card.suit == top_card.suit) and card.face in ['2','3']:
                    return True
                return False
        if self.game_state["effect"].get("name") == "BLOCK":
            if top_card.face == '4':
                return True
            return False
        if self.game_state["effect"].get("name") == "DEMAND SUIT":
            if card.suit == self.game_state["effect"]["suit"] or card.face == 'A':
                return True
            return False
        if self.game_state["effect"].get("name") == "DEMAND FACE":
            if card.face == self.game_state["effect"]["face"] or card.face == 'J':
                return True
            return False
        if len(self.game_state["drawn"]) > 0:
            if card in self.game_state["drawn"] and (card.face == top_card.face or card.suit == top_card.suit or card.face == 'Q'):
                return True
            return False
        if self.game_state["effect"].get("name") == None:
            if card.face == top_card.face or card.suit == top_card.suit or card.face == 'Q':
                return True
            return False
        return False

    def add_effect(self, card, suit = None, face = None):
        if card.face in ['5', '6', '7', '8', '9', 'T', 'Q']:
            self.game_state["effect"] = {}
            return
        if card.face == 'K' and card.suit in ['C', 'D']:
            self.game_state["effect"] = {}
            return
        if card.face == '2' or card.face == '3':
            if self.game_state["effect"].get("name") == "DRAW":
                self.game_state["effect"]["severity"] += int(card.face)
            else:
                self.game_state["effect"]["name"] = "DRAW"
                self.game_state["effect"]["severity"] = int(card.face)
        elif card.face == '4':
            if self.game_state["effect"].get("name") == "BLOCK":
                self.game_state["effect"]["severity"] += 1
            else:
                self.game_state["effect"]["name"] = "BLOCK"
                self.game_state["effect"]["severity"] = 1
        elif card.face == 'J':
            self.game_state["effect"]["name"] = "DEMAND FACE"
            self.game_state["effect"]["face"] = face
        elif card.face == 'K' and card.suit in ['H', 'S']:
            if self.game_state["effect"].get("name") == "DRAW":
                self.game_state["effect"]["severity"] += 5
            else:
                self.game_state["effect"]["name"] = "DRAW"
                self.game_state["effect"]["severity"] = 5
        elif card.face == 'A':
            self.game_state["effect"]["name"] = "DEMAND SUIT"
            self.game_state["effect"]["suit"] = suit
        return

    def resolve_effect(self):
        player_id = self.game_state["current_turn"]
        if self.game_state["effect"].get("name") == "DRAW":
            for i in range(self.game_state["effect"]["severity"]):
                card = self.draw()
                if card:
                    self.game_state["hands"][player_id].append(card)
            self.game_state["effect"] = {}
        elif self.game_state["effect"].get("name") == "BLOCK":
            self.game_state["blocked"][player_id] += self.game_state["effect"]["severity"]
            self.game_state["effect"] = {}







    def start_game(self):
        print("[MAKAO] start")
        with self.lock:
            if self.game_state["game_started"]:
                print("[INFO] Gra już została rozpoczęta")
                return

            if len(self.players) < 2:
                print("[INFO] Za mało graczy, minimum 2")
                return

            self.game_state["game_started"] = True
            print("[INFO] Start gry (Makao)")
            self.start_round_locked()



    def start_round_locked(self):
        if len(self.players) < 2:
            self.game_state["game_started"] = False
            self.game_state["phase"] = "waiting"
            self.game_state["current_turn"] = None
            print("[INFO] Za mało graczy, nie można rozpocząć rundy")
            return

        deck = DeckSimple(self.settings["number_of_decks"])

        deck.shuffle()
        self.game_state["deck"] = deck
        print("=== START RUNDY ===")

        self.game_state["table"] = [deck.draw()]
        self.game_state["hands"] = {}
        self.game_state["current_turn"] = self.players[0][0]
        self.game_state["played"] = []
        self.game_state["blocked"] = {}
        self.game_state["drawn"] = []
        self.game_state["effect"] = {}
        self.game_state["winners"] = {}
        self.game_state["makao_called"] = {}

        for player in self.players:
            player_id = player[0]
            conn = player[1]
            hand = []
            for i in range(self.settings["starting_cards"]):
                hand.append(self.game_state["deck"].draw())

            self.game_state["hands"][player_id] = hand
            self.game_state["blocked"][player_id] = 0
            self.game_state["makao_called"][player_id] = False

            msg = self.create_msg(
                game="MAKAO",
                msg_type="HAND",
                player_id=player_id,
                data={"cards": [str(card) for card in hand]}
            )
            self.send_to_player(conn, msg)

        self.update_next_turn(0)
        self.send_turn_to_current_player()





    def handle_message(self, msg):
        with self.lock:
            msg_type = msg.get("type")
            player_id = msg.get("player_id")
            data = msg.get("data", {})

            if not self.game_state["game_started"]:
                print("[INFO] Ignoruję ruch, gra nie została rozpoczęta")
                return

            if self.game_state["current_turn"] is None:
                print("[ERROR] Brak aktualnej tury")
                return

            action = msg_type


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


            if action == "MAKAO":
                hand_size = len(self.game_state["hands"][player_id])

                if hand_size == 1:
                    self.game_state["makao_called"][player_id] = True

                    msg = self.create_msg(
                        game="MAKAO",
                        msg_type = "MAKAO",
                        player_id = player_id
                    )

                    self.broadcast(msg)

                    print(f"[MAKAO] Gracz {player_id} powiedział MAKAO")

                else:
                    print("[ERROR] Nie można powiedzieć MAKAO")

                return



            if action == "REPORT_MAKAO":
                target = int(data.get("target"))

                if target is None:
                    return

                hand_size = len(self.game_state["hands"].get(target, []))
                said = self.game_state["makao_called"].get(target, False)

                if hand_size == 1 and not said and target != self.game_state["current_turn"]:
                    for _ in range(5):
                        card = self.draw()
                        if card:
                            self.game_state["hands"][target].append(card)

                    msg = self.create_msg(
                        game="MAKAO",
                        msg_type="REPORT",
                        player_id=target,
                        data={
                        }
                    )

                    self.broadcast(msg)

                return

            if player_id != self.game_state["current_turn"]:
                print ("[ERROR] To nie jest tura tego gracza")
                return

            if action == "PLAY":
                face = data["face"]
                suit = data["suit"]
                demand_face = data.get("face_demand", None)
                demand_suit = data.get("suit_demand", None)
                card = CardSimple(suit, face)
                if card not in self.game_state["hands"][player_id]:
                    print("[ERROR] Nie masz tej karty")
                elif len(self.game_state["drawn"]) > 0 and len(self.game_state["played"]) > 0:
                    print("[ERROR] Nielegalny ruch")
                elif self.check_card_eligibility(card):
                    self.add_effect(card, demand_suit, demand_face)
                    self.game_state["hands"][player_id].remove(card)
                    self.game_state["table"].append(card)
                    self.game_state["played"].append(card)
                    self.send_table_update()
                    if self.check_winner():
                        self.game_state["next_turn"] = None
                        self.game_state["makao_called"][player_id] = False
                        return
                else:
                    print("[ERROR] zła karta")
                self.send_turn_to_current_player()
                return


            if action == "DRAW":
                if len(self.game_state["drawn"]) > 0:
                    print("[ERROR] Nie można pociągnąc więcej niż jednej karty.")
                elif self.game_state["effect"].get("name") in ["DRAW", "BLOCK"]:
                    msg = self.create_msg(
                        game="MAKAO",
                        msg_type="EFFECT DRAW",
                        player_id=player_id
                    )
                    self.send_to_player(self.get_player_conn(self.game_state["current_turn"]), msg)
                else:
                    card = self.draw()
                    if card:
                        self.game_state["hands"][player_id].append(card)
                    self.game_state["makao_called"][player_id] = False
                self.send_table_update()
                self.send_turn_to_current_player()
                return


            if action == "END TURN":
                if len(self.game_state["played"]) == 0 and len(self.game_state["drawn"]) == 0 and not self.game_state["effect"].get("name") in ["DRAW", "BLOCK"]:
                    print("[ERROR] Nie można skończyć tury")
                else:
                    if self.game_state["effect"].get("name") in ["DRAW", "BLOCK"] and len(self.game_state["played"]) == 0:
                        self.resolve_effect()
                    if self.game_state["table"][-1] == CardSimple('S', 'K'):
                        current_index = self.get_player_index(self.game_state["current_turn"])
                        self.game_state["current_turn"] = self.get_previous(current_index)
                    else:
                        self.game_state["current_turn"] = self.game_state["next_turn"]
                        current_index = self.get_player_index(self.game_state["current_turn"])
                        self.update_next_turn(current_index)
                    self.game_state["played"] = []
                    self.game_state["drawn"] = []
                    self.send_table_update()
                self.send_turn_to_current_player()
                return


            if action == "ERROR":
                print("[ERROR] Gracz użył nieznanego ruchu.")
                self.send_turn_to_current_player()
                return
            return





