import socket
import threading
import json

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"
FORMAT = 'utf-8'

def create_msg(game, msg_type, player_id=None, data=None, chat=None):
    return {
    	"game": game, #POKER albo MAKAO
        "type": msg_type, #MOVE, ERROR, CHAT, DISCONNECT
        "player_id": player_id,
        "data": data or {}, #action: (BET, CALL, FOLD) amount: wartosc betu
        "chat": chat
    }


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

players = []

def msg_handle_poker():
	pass

def msg_handle_makao():
	pass


def handle_client(conn, addr):
	print(f"New player joined: {addr}")
	players.append((threading.active_count(), conn, addr)) #player_id, connection, addres
	connected = True
	while connected:
		msg_length = conn.recv(HEADER).decode(FORMAT).strip()
		if msg_length:
			msg_length = int(msg_length)
			msg_str = conn.recv(msg_length).decode(FORMAT)
			msg = json.loads(msg_str)
			game = msg.get("game")

		if game == "POKER":
			msg_handle_poker()
		elif game == "MAKAO":
			msg_handle_makao()

def start():
	server.listen()
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr))
		thread.start()