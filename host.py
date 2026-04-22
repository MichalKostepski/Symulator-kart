import socket
import threading
import json
import random
from deck import Deck
from itertools import combinations

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"
FORMAT = 'utf-8'


def create_msg(game, msg_type, player_id=None, data=None, chat=None):
    return {
        "game": game,
        "type": msg_type,
        "player_id": player_id,
        "data": data or {},
        "chat": chat
    }


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

players = []  # [(player_id, conn, addr)]

# Game state
game_state = {
    "deck": None,
    "hands": {},
    "community_cards": [],
    "pot": 0,
    "current_bet": 0,
    "phase": "waiting",
    "blind_amount": 10,
    "blind_player": 0,           # index w liście players
    "current_turn": None,        # index w liście players
    "round_bets": {},
    "folded_players": set(),
    "players_acted": set(),
    "game_started": False,      # kto wykonał ruch w bieżącej fazie
}


def send_to_player(conn, msg):
    msg_str = json.dumps(msg)
    message = msg_str.encode(FORMAT)

    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))

    conn.send(send_length)
    conn.send(message)


def broadcast(msg):	
    for _, conn, _ in players:
        send_to_player(conn, msg)


def get_active_player_ids():
    return [
        player_id for player_id, _, _ in players
        if player_id not in game_state["folded_players"]
    ]

from itertools import combinations


RANK_MAP = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "T": 10,
    "J": 11, "Q": 12, "K": 13, "A": 14
}


def parse_card(card):
    """
    Obsługuje formaty:
    - 'AH', '10S', 'A♠'
    - '2 of diamonds', 'jack of hearts', itd.
    Zwraca (value, suit), np. (14, 'S')
    """
    card_str = str(card).strip().lower()

    # przypadek 1: format tekstowy, np. "2 of diamonds"
    if " of " in card_str:
        rank_str, suit_str = card_str.split(" of ")

        rank_map_text = {
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "jack": 11,
            "queen": 12,
            "king": 13,
            "ace": 14
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

    # przypadek 2: format skrócony, np. "AH", "10D", "A♠"
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

def is_straight(values):
    """
    values: lista wartości kart, np. [14, 13, 12, 11, 10]
    Zwraca (True, najwyższa_karta_straita) albo (False, None)
    Obsługuje też wheel: A-2-3-4-5
    """
    unique_values = sorted(set(values), reverse=True)

    if len(unique_values) != 5:
        return (False, None)

    # zwykły straight, np. 10-J-Q-K-A
    if unique_values[0] - unique_values[4] == 4:
        return (True, unique_values[0])

    # wheel: A-2-3-4-5
    if unique_values == [14, 5, 4, 3, 2]:
        return (True, 5)

    return (False, None)


def evaluate_5cards(cards5):
    """
    cards5: lista 5 kart
    Zwraca tuple porównywalne lexicograficznie.
    Im większe, tym lepszy układ.

    Kategorie:
    8 - straight flush
    7 - kareta
    6 - full house
    5 - flush
    4 - straight
    3 - trójka
    2 - dwie pary
    1 - jedna para
    0 - wysoka karta
    """
    parsed = [parse_card(card) for card in cards5]
    values = sorted([v for v, s in parsed], reverse=True)
    suits = [s for v, s in parsed]

    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1

    # sortujemy po:
    # najpierw liczba powtórzeń malejąco,
    # potem wartość karty malejąco
    count_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))

    is_flush = len(set(suits)) == 1
    straight, straight_high = is_straight(values)

    # Straight flush
    if is_flush and straight:
        return (8, straight_high)

    # Four of a kind
    if count_items[0][1] == 4:
        four_value = count_items[0][0]
        kicker = count_items[1][0]
        return (7, four_value, kicker)

    # Full house
    if count_items[0][1] == 3 and count_items[1][1] == 2:
        three_value = count_items[0][0]
        pair_value = count_items[1][0]
        return (6, three_value, pair_value)

    # Flush
    if is_flush:
        return (5, *values)

    # Straight
    if straight:
        return (4, straight_high)

    # Three of a kind
    if count_items[0][1] == 3:
        three_value = count_items[0][0]
        kickers = sorted([v for v in values if v != three_value], reverse=True)
        return (3, three_value, *kickers)

    # Two pair
    if count_items[0][1] == 2 and count_items[1][1] == 2:
        pair1 = max(count_items[0][0], count_items[1][0])
        pair2 = min(count_items[0][0], count_items[1][0])
        kicker = [v for v in values if v != pair1 and v != pair2][0]
        return (2, pair1, pair2, kicker)

    # One pair
    if count_items[0][1] == 2:
        pair_value = count_items[0][0]
        kickers = sorted([v for v in values if v != pair_value], reverse=True)
        return (1, pair_value, *kickers)

    # High card
    return (0, *values)


def get_best_hand(cards7):
    """
    Z 7 kart wybiera najlepszy układ 5-kartowy.
    Zwraca:
    (best_score, best_5cards)
    """
    best_score = None
    best_combo = None

    for combo in combinations(cards7, 5):
        score = evaluate_5cards(combo)
        if best_score is None or score > best_score:
            best_score = score
            best_combo = combo

    return best_score, best_combo


def hand_name(score):
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

def get_next_active_turn(start_index):
    """
    Zwraca index kolejnego aktywnego gracza od start_index+1.
    """
    if not players:
        return None

    next_index = start_index
    while True:
        next_index = (next_index + 1) % len(players)
        next_player_id = players[next_index][0]

        if next_player_id not in game_state["folded_players"]:
            return next_index


def reset_betting_round():
    game_state["current_bet"] = 0
    game_state["players_acted"] = set()

    for player_id, _, _ in players:
        if player_id not in game_state["folded_players"]:
            game_state["round_bets"][player_id] = 0


def send_turn_to_current_player():
    turn_index = game_state["current_turn"]
    turn_player_id, turn_conn, _ = players[turn_index]

    turn_msg = create_msg(
        game="POKER",
        msg_type="TURN",
        player_id=turn_player_id,
        data={
            "current_bet": game_state["current_bet"],
            "pot": game_state["pot"],
            "phase": game_state["phase"],
            "community_cards": [str(card) for card in game_state["community_cards"]],
            "your_bet": game_state["round_bets"].get(turn_player_id, 0)
        }
    )

    send_to_player(turn_conn, turn_msg)
    print(f"[TURN] Tura gracza {turn_player_id}")


def send_table_update():
    msg = create_msg(
        game="POKER",
        msg_type="TABLE",
        data={
            "phase": game_state["phase"],
            "pot": game_state["pot"],
            "current_bet": game_state["current_bet"],
            "community_cards": [str(card) for card in game_state["community_cards"]],
            "folded_players": list(game_state["folded_players"])
        }
    )
    broadcast(msg)


def award_pot_to_winner(winner_id, reason="WIN"):
    msg = create_msg(
        game="POKER",
        msg_type="WINNER",
        player_id=winner_id,
        data={
            "winner": winner_id,
            "pot": game_state["pot"],
            "reason": reason,
            "community_cards": [str(card) for card in game_state["community_cards"]],
        }
    )
    broadcast(msg)
    print(f"[WINNER] Gracz {winner_id} wygrywa pulę {game_state['pot']} ({reason})")

    # przygotowanie kolejnej rundy
    game_state["blind_player"] = (game_state["blind_player"] + 1) % len(players)
    start_round()


def showdown():
    active_players = get_active_player_ids()

    results = []

    for pid in active_players:
        cards7 = game_state["hands"][pid] + game_state["community_cards"]
        best_score, best_combo = get_best_hand(cards7)

        results.append({
            "player_id": pid,
            "score": best_score,
            "best_combo": [str(card) for card in best_combo],
            "hand_name": hand_name(best_score)
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

        msg = create_msg(
            game="POKER",
            msg_type="WINNER",
            player_id=winner["player_id"],
            data={
                "winner": winner["player_id"],
                "pot": game_state["pot"],
                "reason": "SHOWDOWN",
                "community_cards": [str(card) for card in game_state["community_cards"]],
                "hand_name": winner["hand_name"],
                "best_combo": winner["best_combo"]
            }
        )
        broadcast(msg)

        print(f"[WINNER] Gracz {winner['player_id']} wygrywa pulę {game_state['pot']}")
        print(f"[WINNER] Układ: {winner['hand_name']}")

    else:
        winner_ids = [w["player_id"] for w in winners]

        msg = create_msg(
            game="POKER",
            msg_type="WINNER",
            data={
                "winner": winner_ids,
                "pot": game_state["pot"],
                "reason": "SHOWDOWN_TIE",
                "community_cards": [str(card) for card in game_state["community_cards"]],
                "hand_name": winners[0]["hand_name"],
                "best_combo": [w["best_combo"] for w in winners]
            }
        )
        broadcast(msg)

        print(f"[WINNER] Remis między graczami: {winner_ids}")
        print(f"[WINNER] Najlepszy układ: {winners[0]['hand_name']}")

    game_state["blind_player"] = (game_state["blind_player"] + 1) % len(players)
    start_round()

def advance_phase():
    deck = game_state["deck"]

    if game_state["phase"] == "preflop":
        game_state["phase"] = "flop"
        game_state["community_cards"] = [deck.draw(), deck.draw(), deck.draw()]
        print(f"[PHASE] FLOP: {game_state['community_cards']}")

    elif game_state["phase"] == "flop":
        game_state["phase"] = "turn"
        game_state["community_cards"].append(deck.draw())
        print(f"[PHASE] TURN: {game_state['community_cards']}")

    elif game_state["phase"] == "turn":
        game_state["phase"] = "river"
        game_state["community_cards"].append(deck.draw())
        print(f"[PHASE] RIVER: {game_state['community_cards']}")

    elif game_state["phase"] == "river":
        game_state["phase"] = "showdown"
        print("[PHASE] SHOWDOWN")
        send_table_update()
        showdown()
        return

    reset_betting_round()

    # uproszczenie:
    # nową fazę zaczyna pierwszy aktywny gracz po blindzie
    start_index = game_state["blind_player"]
    game_state["current_turn"] = get_next_active_turn(start_index)

    send_table_update()
    send_turn_to_current_player()


def is_betting_round_over():
    active_players = get_active_player_ids()

    if len(active_players) <= 1:
        return True

    # każdy aktywny gracz musi wykonać ruch w tej fazie
    for pid in active_players:
        if pid not in game_state["players_acted"]:
            return False

    # każdy aktywny gracz musi mieć wyrównany bet
    for pid in active_players:
        if game_state["round_bets"].get(pid, 0) != game_state["current_bet"]:
            return False

    return True


def start_round():
    deck = Deck()
    deck.shuffle()

    print("=== START RUNDY ===")

    game_state["deck"] = deck
    game_state["hands"] = {}
    game_state["community_cards"] = []
    game_state["pot"] = 0
    game_state["current_bet"] = 0
    game_state["phase"] = "preflop"
    game_state["round_bets"] = {}
    game_state["folded_players"] = set()
    game_state["players_acted"] = set()

    blind_index = game_state["blind_player"]

    # rozdanie kart
    for player_id, conn, _ in players:
        hand = [deck.draw(), deck.draw()]
        game_state["hands"][player_id] = hand
        game_state["round_bets"][player_id] = 0

        msg = create_msg(
            game="POKER",
            msg_type="HAND",
            player_id=player_id,
            data={
                "cards": [str(card) for card in hand]
            }
        )
        send_to_player(conn, msg)

    # blind
    blind_player_id, _, _ = players[blind_index]
    blind_amount = game_state["blind_amount"]

    game_state["round_bets"][blind_player_id] = blind_amount
    game_state["pot"] = blind_amount
    game_state["current_bet"] = blind_amount

    print(f"[BLIND] Gracz {blind_player_id} wpłaca blind: {blind_amount}")

    # pierwszy ruch ma gracz po blindzie
    game_state["current_turn"] = get_next_active_turn(blind_index)

    send_table_update()
    send_turn_to_current_player()


def msg_handle_poker(msg):
    msg_type = msg.get("type")
    player_id = msg.get("player_id")
    data = msg.get("data", {})

    if msg_type != "MOVE":
        return

    action = data.get("action")
    print(f"[MOVE] Gracz {player_id} wykonał ruch: {action}")

    # sprawdzamy czy to na pewno jego kolej
    current_turn_index = game_state["current_turn"]
    current_turn_player_id = players[current_turn_index][0]

    if player_id != current_turn_player_id:
        print(f"[ERROR] To nie tura gracza {player_id}")
        return

    if player_id in game_state["folded_players"]:
        print(f"[ERROR] Gracz {player_id} już spasował")
        return

    if action == "CALL":
        amount_to_call = game_state["current_bet"] - game_state["round_bets"][player_id]

        if amount_to_call < 0:
            amount_to_call = 0

        game_state["round_bets"][player_id] += amount_to_call
        game_state["pot"] += amount_to_call
        game_state["players_acted"].add(player_id)

        print(f"[CALL] Gracz {player_id} dopłaca: {amount_to_call}")
        print(f"[POT] Nowa pula: {game_state['pot']}")

    elif action == "FOLD":
        game_state["folded_players"].add(player_id)
        game_state["players_acted"].add(player_id)
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

        if new_bet <= game_state["current_bet"]:
            print(f"[ERROR] Raise musi być większy niż current_bet")
            return

        amount_to_add = new_bet - game_state["round_bets"][player_id]
        game_state["round_bets"][player_id] = new_bet
        game_state["current_bet"] = new_bet
        game_state["pot"] += amount_to_add

        # po raise wszyscy pozostali muszą znowu odpowiedzieć,
        # więc resetujemy players_acted do tylko tego gracza
        game_state["players_acted"] = {player_id}

        print(f"[RAISE] Gracz {player_id} podbija do: {new_bet}")
        print(f"[POT] Nowa pula: {game_state['pot']}")
        print(f"[BET] Nowy current_bet: {game_state['current_bet']}")

    else:
        print(f"[ERROR] Nieznana akcja: {action}")
        return

    send_table_update()

    active_players = get_active_player_ids()

    if len(active_players) == 1:
        winner = active_players[0]
        award_pot_to_winner(winner, reason="ALL_FOLDED")
        return

    if is_betting_round_over():
        print("[INFO] Koniec rundy licytacji")
        advance_phase()
        return

    next_turn = get_next_active_turn(game_state["current_turn"])
    game_state["current_turn"] = next_turn
    send_turn_to_current_player()


def msg_handle_makao(msg):
    print("Odebrano wiadomość makao:", msg)


def handle_client(conn, addr):
    print(f"New player joined: {addr}")

    player_id = len(players) + 1
    players.append((player_id, conn, addr))

    print(f"[INFO] Gracz {player_id} dołączył")


    connected = True
    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT).strip()

            if not msg_length:
                continue

            msg_length = int(msg_length)
            msg_str = conn.recv(msg_length).decode(FORMAT)
            msg = json.loads(msg_str)
            game = msg.get("game")

            if game == "POKER":
                msg_handle_poker(msg)
            elif game == "MAKAO":
                msg_handle_makao(msg)

        except Exception as e:
            print(f"[DISCONNECT] Błąd klienta {player_id}: {e}")
            connected = False

    conn.close()

def server_commands():
    while True:
        cmd = input().strip().lower()

        if cmd == "start":
            if game_state["game_started"]:
                print("[INFO] Gra już została rozpoczęta")
                continue

            if len(players) < 2:
                print("[INFO] Za mało graczy, minimum 2")
                continue

            game_state["game_started"] = True
            print("[INFO] Start gry")
            start_round()

def start():
    server.listen()
    print(f"Server listening on {SERVER}:{PORT}")
    print("Wpisz 'start', aby rozpocząć grę, gdy gracze już dołączą.")

    command_thread = threading.Thread(target=server_commands, daemon=True)
    command_thread.start()

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

start()
