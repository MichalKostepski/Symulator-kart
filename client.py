import socket
import json

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

my_player_id = None


def create_msg(game, msg_type, player_id=None, data=None, chat=None):
    return {
        "game": game,
        "type": msg_type,
        "player_id": player_id,
        "data": data or {},
        "chat": chat
    }


def msg_handle_poker(msg):
    global my_player_id

    msg_type = msg.get("type")
    data = msg.get("data", {})
    player_id = msg.get("player_id")
    chat = msg.get("chat")

    # ===== HAND =====
    if msg_type == "HAND":
        my_player_id = player_id
        cards = data.get("cards", [])
        print("\n[POKER] Twoje karty:", cards)

    # ===== TABLE UPDATE =====
    elif msg_type == "TABLE":
        phase = data.get("phase")
        pot = data.get("pot")
        current_bet = data.get("current_bet")
        community_cards = data.get("community_cards", [])
        folded = data.get("folded_players", [])

        print("\n========== STÓŁ ==========")
        print("Faza:", phase)
        print("Karty wspólne:", community_cards)
        print("Pula:", pot)
        print("Aktualny bet:", current_bet)
        print("Spasowani gracze:", folded)
        print("==========================")

    # ===== TURN =====
    elif msg_type == "TURN":
        # tylko jeśli to nasza tura
        if player_id != my_player_id:
            return

        print("\n[POKER] Twoja kolej!")
        print("Faza:", data.get("phase"))
        print("Karty wspólne:", data.get("community_cards", []))
        print("Aktualny bet:", data.get("current_bet"))
        print("Twój wkład:", data.get("your_bet"))
        print("Pula:", data.get("pot"))

        action = input("Ruch (CALL/FOLD/RAISE): ").strip().upper()

        move_data = {"action": action}

        if action == "RAISE":
            amount = input("Podaj nowy bet (np. 30): ").strip()
            try:
                move_data["amount"] = int(amount)
            except ValueError:
                print("[CLIENT] Zła liczba -> FOLD")
                move_data = {"action": "FOLD"}

        move_msg = create_msg(
            game="POKER",
            msg_type="MOVE",
            player_id=my_player_id,
            data=move_data
        )
        send(move_msg)

    # ===== WINNER =====
    elif msg_type == "WINNER":
        winner = data.get("winner")
        pot = data.get("pot")
        reason = data.get("reason")
        community_cards = data.get("community_cards", [])
        hand_name = data.get("hand_name")
        best_combo = data.get("best_combo")

        print("\n***** KONIEC ROZDANIA *****")

        if isinstance(winner, list):
            print("Remis między graczami:", winner)
        else:
            print("Zwycięzca: gracz", winner)

        print("Pula:", pot)
        print("Powód:", reason)
        print("Karty wspólne:", community_cards)

        if hand_name:
            print("Najlepszy układ:", hand_name)

        if best_combo:
            print("Najlepsze 5 kart:", best_combo)

        print("***************************")

    # ===== MOVE (info o innych graczach) =====
    elif msg_type == "MOVE":
        action = data.get("action")
        amount = data.get("amount")
        print(f"[POKER] Gracz {player_id} zrobił: {action} {amount if amount else ''}")

    # ===== CHAT =====
    elif msg_type == "CHAT":
        print(f"[CHAT] Gracz {player_id}: {chat}")

    # ===== ERROR =====
    elif msg_type == "ERROR":
        print("[ERROR]:", data)

    # ===== DISCONNECT =====
    elif msg_type == "DISCONNECT":
        print(f"[INFO] Gracz {player_id} się rozłączył")

    else:
        print("[POKER] Nieznany typ wiadomości:", msg_type)

def send(msg):
    msg_str = json.dumps(msg)
    message = msg_str.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)


def receive():
    while True:
        msg_length = client.recv(HEADER).decode(FORMAT).strip()

        if msg_length:
            msg_length = int(msg_length)
            msg_str = client.recv(msg_length).decode(FORMAT)
            msg = json.loads(msg_str)
            game = msg.get("game")

            if game == "POKER":
                msg_handle_poker(msg)
            elif game == "MAKAO":
                msg_handle_makao(msg)


receive()
