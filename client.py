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

def create_msg(game, msg_type, player_id=None, data=None, chat=None):
    return {
    	"game": game, #POKER albo MAKAO
        "type": msg_type, #MOVE, ERROR, CHAT, DISCONNECT
        "player_id": player_id,
        "data": data or {}, #action: (BET, CALL, FOLD) amount: wartosc betu
        "chat": chat
    }

def msg_handle_poker():
	pass

def msg_handle_makao():
	pass



def send(msg):
	msg_str = json.dumps(msg)
	message = msg_str.encode(FORMAT)
	msg_length = len(message)
	send_length = str(msg_length).encode(FORMAT)
	send_length += b' ' * (HEADER - len(send_length))
	client.send(send_length)
	client.send(message)

def recive(msg):
	msg_length = client.recv(HEADER).decode(FORMAT).strip()
		if msg_length:
			msg_length = int(msg_length)
			msg_str = client.recv(msg_length).decode(FORMAT)
			msg = json.loads(msg_str)
			game = msg.get("game")

		if game == "POKER":
			msg_handle_poker()
		elif game == "MAKAO":
			msg_handle_makao()