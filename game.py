from abc import ABC, abstractmethod
import threading


class Game(ABC):

    def __init__(self, send_json, create_msg):
        self.send_json = send_json
        self.create_msg = create_msg

        self.lock = threading.RLock()

        self.players = [] # [(player_id, conn, addr, is_bot, bot)]
        self.next_player_id = 1

    # =========================
    # Players
    # =========================

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

    # =========================
    # Messaging
    # =========================

    def send_to_player(self, conn, msg):
        self.send_json(conn, msg)

    def broadcast(self, msg):
        disconnected = []

        for player_id, conn, _, is_bot, bot in self.players:
            if is_bot:
                continue
            try:
                self.send_to_player(conn, msg)
            except:
                disconnected.append(player_id)

        for pid in disconnected:
            self.remove_player(pid)

    # =========================
    # Abstract methods
    # =========================

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

    