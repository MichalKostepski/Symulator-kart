from abc import ABC, abstractmethod
import threading


class Game(ABC):

    def __init__(self, send_json, create_msg):
        self.send_json = send_json
        self.create_msg = create_msg

        self.lock = threading.RLock()

        self.players = []
        self.next_player_id = 1





    def add_player(self, conn, addr):
        with self.lock:
            player_id = self.next_player_id
            self.next_player_id += 1

            self.players.append((player_id, conn, addr, False, None))

            print(f"[{self.name}] Gracz {player_id} dołączył")

            return player_id

    def remove_player(self, player_id):
        with self.lock:
            self.players = [
                p for p in self.players
                if p[0] != player_id
            ]

            print(f"[{self.name}] Gracz {player_id} opuścił grę")





    def send_to_player(self, conn, msg):
        self.send_json(conn, msg)

    def broadcast(self, msg):
        disconnected = []

        for player in self.players:




            player_id = player[0]
            conn = player[1]
            is_bot = len(player) >= 4 and player[3]

            if is_bot:
                continue
            try:
                self.send_to_player(conn, msg)
            except Exception:
                disconnected.append(player_id)

        for pid in disconnected:
            self.remove_player(pid)





    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def handle_message(self, msg):
        pass

    @abstractmethod
    def start_game(self):
        pass

