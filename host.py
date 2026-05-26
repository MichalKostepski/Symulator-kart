import socket
import threading
import json

from poker import PokerGame
from makao import MakaoGame

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"


def recv_exact(conn, length):
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data


def send_json(conn, msg):
    if conn == None:
        return
    msg_str = json.dumps(msg)
    message = msg_str.encode(FORMAT)

    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))

    conn.sendall(send_length)
    conn.sendall(message)


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

poker_game = PokerGame(send_json=send_json, create_msg=create_msg)
makao_game = MakaoGame(send_json=send_json, create_msg=create_msg)

def msg_handle_makao(msg):
    print("Odebrano wiadomość MAKAO:", msg)


def handle_client(conn, addr):

    current_game = None
    player_id = None

    connected = True

    while connected:

        try:
            header_data = recv_exact(conn, HEADER)

            if not header_data:
                break

            msg_length_str = header_data.decode(FORMAT).strip()

            if not msg_length_str:
                continue

            msg_length = int(msg_length_str)

            msg_data = recv_exact(conn, msg_length)

            if not msg_data:
                break

            msg_str = msg_data.decode(FORMAT)

            msg = json.loads(msg_str)

            game = msg.get("game")
            msg_type = msg.get("type")

            # =========================
            # JOIN GAME
            # =========================

            if game == "SYSTEM":

                if msg_type == "JOIN":

                    target = msg["data"]["target_game"]

                    if target in games:

                        current_game = games[target]

                        player_id = current_game.add_player(conn, addr)

                        send_json(conn, create_msg(
                            game="SYSTEM",
                            msg_type="JOINED",
                            player_id=player_id,
                            data={
                                "game": target
                            }
                        ))

                        print(f"[INFO] Player joined {target}")

                continue

            # =========================
            # NORMAL GAME MESSAGE
            # =========================

            if current_game:
                current_game.handle_message(msg)

        except Exception as e:
            print(f"[DISCONNECT] {addr}: {e}")
            connected = False

    # =========================
    # DISCONNECT
    # =========================

    if current_game and player_id:
        current_game.remove_player(player_id)

    conn.close()


def server_commands():

    while True:

        cmd = input().strip().lower()

        if cmd == "start poker":
            games["POKER"].start_game()

        elif cmd == "start makao":
            games["MAKAO"].start_game()

        elif cmd == "players poker":
            print(games["POKER"].players)

        elif cmd == "players makao":
            print(games["MAKAO"].players)

        elif cmd == "add makao bot":
            games["MAKAO"].add_bot()


def start():
    server.listen()
    print(f"Server listening on {SERVER}:{PORT}")
    print("Wpisz 'start poker' lub 'start makao', aby rozpocząć grę, gdy gracze już dołączą.")
    print("Wpisz 'add makao bot', aby dodać bota do Makao")

    command_thread = threading.Thread(target=server_commands, daemon=True)
    command_thread.start()

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()

games = {
    "POKER": PokerGame(send_json, create_msg),
    "MAKAO": MakaoGame(send_json, create_msg)
}

start()
