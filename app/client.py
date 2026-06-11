import os
import math

import socket
import json
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import colorchooser
from stats_manager import StatsManager

HEADER = 64
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"


def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"




DEFAULT_SERVER = get_local_ip()
ADDR = (DEFAULT_SERVER, PORT)






def create_msg(game, msg_type, player_id=None, data=None, chat=None):
    return {
        "game": game,
        "type": msg_type,
        "player_id": player_id,
        "data": data or {},
        "chat": chat,
    }


def recv_exact(sock, length):
    chunks = []
    received = 0

    while received < length:
        chunk = sock.recv(length - received)
        if not chunk:
            return None
        chunks.append(chunk)
        received += len(chunk)

    return b"".join(chunks)


def unique_list(items):
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result






class CardGameClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker / Makao - Klient")
        self.bg_color = "#0B3D2E"
        self.setup_window()
        self.root.configure(bg=self.bg_color)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)


        self.client = None
        self.connected = False
        self.running = True
        self.receive_thread = None
        self.connected_server = None
        self.server_var = tk.StringVar(value=DEFAULT_SERVER)
        self.status_var = tk.StringVar(value="Nie połączono z serwerem")


        self.active_game = None
        self.my_player_id = None
        self.log_text = None
        self.chat_entry = None


        self.poker_hand_cards = []
        self.poker_community_cards = []
        self.poker_phase = "-"
        self.poker_pot = 0
        self.poker_current_bet = 0
        self.poker_your_bet = 0
        self.poker_folded_players = []
        self.poker_chips_var = tk.StringVar(value="Żetony: -")

        self.poker_player_var = tk.StringVar(value="Gracz: -")
        self.poker_phase_var = tk.StringVar(value="Faza: -")
        self.poker_pot_var = tk.StringVar(value="Pula: 0")
        self.poker_current_bet_var = tk.StringVar(value="Aktualny bet: 0")
        self.poker_your_bet_var = tk.StringVar(value="Twój wkład: 0")
        self.poker_folded_var = tk.StringVar(value="Spasowani: -")


        self.poker_players = []
        self.poker_turn_player = None
        self.poker_blind_player = None
        self.poker_round_bets = {}
        self.poker_table_canvas = None

        self.poker_hand_frame = None
        self.poker_community_frame = None
        self.poker_raise_entry = None
        self.poker_call_button = None
        self.poker_fold_button = None
        self.poker_raise_button = None


        self.makao_hand_cards = []
        self.makao_table_card = None
        self.makao_players = []
        self.makao_turn_player = None
        self.makao_played_this_turn = []
        self.makao_drawn_this_turn = []
        self.makao_effect = {}
        self.selected_makao_card = None

        self.makao_player_var = tk.StringVar(value="Gracz: -")
        self.makao_turn_var = tk.StringVar(value="Tura: -")
        self.makao_table_var = tk.StringVar(value="Karta na stole: -")
        self.makao_effect_var = tk.StringVar(value="Efekt: brak")
        self.makao_selected_card_var = tk.StringVar(value="Wybrana karta: -")
        self.makao_drawn_var = tk.StringVar(value="Dobrane w tej turze: -")
        self.makao_played_var = tk.StringVar(value="Zagrane w tej turze: -")
        self.makao_report_var = tk.StringVar(value="")
        self.makao_report_target = tk.StringVar(value="")


        self.makao_hand_frame = None
        self.makao_table_card_frame = None
        self.makao_players_frame = None
        self.makao_play_button = None
        self.makao_draw_button = None
        self.makao_end_button = None
        self.face_demand_var = tk.StringVar(value="5")
        self.suit_demand_var = tk.StringVar(value="C")

        self.stats = StatsManager()
        self.menu_stats_var = tk.StringVar(value=self.stats.format_stats())

        self.refresh_menu_stats()
        self.show_menu()
        self.connect_to_server(show_errors=False)





    def setup_window(self):
        target_width = 1920
        target_height = 1080
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(target_width, max(900, screen_width - 40))
        height = min(target_height, max(620, screen_height - 80))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(900, width), min(600, height))
        self.ui_scale = max(0.78, min(width / target_width, height / target_height, 1.0))
        try:
            if screen_width >= target_width and screen_height >= target_height:
                self.root.state("zoomed")
        except tk.TclError:
            pass

    def scaled(self, value):
        return max(1, int(value * self.ui_scale))

    def make_screen(self, padx=24, pady=18):
        holder = tk.Frame(self.root, bg=self.bg_color)
        holder.pack(fill="both", expand=True)
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        canvas = tk.Canvas(holder, bg=self.bg_color, highlightthickness=0, bd=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        vertical = tk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        vertical.grid(row=0, column=1, sticky="ns")

        horizontal = tk.Scrollbar(holder, orient="horizontal", command=canvas.xview)
        horizontal.grid(row=1, column=0, sticky="ew")

        canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        frame = tk.Frame(canvas, bg=self.bg_color, padx=padx, pady=pady)
        window_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        def refresh_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_frame(event):
            requested_width = frame.winfo_reqwidth()
            requested_height = frame.winfo_reqheight()
            canvas.itemconfigure(window_id, width=max(event.width, requested_width), height=max(event.height, requested_height))
            refresh_region()

        def wheel(event):
            delta = -1 if event.delta > 0 else 1
            canvas.yview_scroll(delta * 3, "units")

        frame.bind("<Configure>", refresh_region)
        canvas.bind("<Configure>", fit_frame)
        canvas.bind("<Enter>", lambda event: canvas.bind_all("<MouseWheel>", wheel))
        canvas.bind("<Leave>", lambda event: canvas.unbind_all("<MouseWheel>"))

        return frame

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.log_text = None

    def make_button(self, parent, text, command, bg="#E9C46A", fg="#10231D", width=18):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 13, "bold"),
            bg=bg,
            fg=fg,
            activebackground="#F4D35E",
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            width=width,
            cursor="hand2",
        )

    def make_panel(self, parent, bg="#123F32", padx=18, pady=18):
        return tk.Frame(
            parent,
            bg=bg,
            padx=padx,
            pady=pady,
            highlightthickness=1,
            highlightbackground="#2A6F5A",
        )

    def make_title(self, parent, text, size=30):
        return tk.Label(
            parent,
            text=text,
            font=("Arial", size, "bold"),
            fg="#F8F7F2",
            bg=self.bg_color,
        )

    def make_small_label(self, parent, text=None, textvariable=None, bg="#123F32", size=12, bold=False):
        return tk.Label(
            parent,
            text=text,
            textvariable=textvariable,
            font=("Arial", size, "bold" if bold else "normal"),
            fg="#F8F7F2",
            bg=bg,
            justify="left",
            wraplength=230,
        )

    def refresh_menu_stats(self):
        self.menu_stats_var.set(self.stats.format_stats())

    def normalize_card_code_for_image(self, card):
        if card is None:
            return "BACK"

        if isinstance(card, dict):
            face = str(card.get("face", "")).strip().upper()
            suit = str(card.get("suit", "")).strip().upper()
            raw = (face + suit).strip()
        else:
            raw = str(card).strip()

        if not raw:
            return "BACK"

        raw = raw.replace("♥", "H").replace("♦", "D").replace("♣", "C").replace("♠", "S")
        raw_upper = raw.upper().replace("_", " ").replace("-", " ").strip()

        if raw_upper in ["", "-", "—", "BACK", "NONE"]:
            return "BACK"

        face_map = {
            "A": "A", "ACE": "A", "AS": "A",
            "K": "K", "KING": "K", "KRÓL": "K", "KROL": "K",
            "Q": "Q", "QUEEN": "Q", "DAMA": "Q",
            "J": "J", "JACK": "J", "WALET": "J",
            "T": "T", "10": "T", "TEN": "T",
        }

        suit_map = {
            "H": "H", "HEART": "H", "HEARTS": "H", "KIER": "H", "KIERA": "H",
            "D": "D", "DIAMOND": "D", "DIAMONDS": "D", "KARO": "D",
            "C": "C", "CLUB": "C", "CLUBS": "C", "TREFL": "C", "TREFLE": "C",
            "S": "S", "SPADE": "S", "SPADES": "S", "PIK": "S", "PIKI": "S",
        }


        if " OF " in raw_upper:
            face_part, suit_part = raw_upper.split(" OF ", 1)
            face_part = face_part.strip()
            suit_part = suit_part.strip()
            face = face_map.get(face_part, face_part)
            suit = suit_map.get(suit_part)
            if suit:
                return face + suit


        parts = raw_upper.split()
        if len(parts) >= 2:
            face_part = parts[0]
            suit_part = parts[-1]
            face = face_map.get(face_part, face_part)
            suit = suit_map.get(suit_part)
            if suit:
                return face + suit


        if raw_upper.startswith("10") and len(raw_upper) >= 3:
            return "T" + raw_upper[-1]


        if len(raw_upper) >= 2:
            face = raw_upper[:-1]
            suit = raw_upper[-1]
            face = face_map.get(face, face)
            if suit in ["H", "D", "C", "S"]:
                return face + suit

        return "BACK"

    def card_code_to_filename(self, card):
        card_code = self.normalize_card_code_for_image(card)

        if card_code == "BACK":
            return "card_back.png"

        suit_map = {
            "H": "hearts",
            "D": "diamonds",
            "C": "clubs",
            "S": "spades",
        }

        value_map = {
            "A": "A",
            "K": "K",
            "Q": "Q",
            "J": "J",
            "T": "10",
        }

        if len(card_code) < 2:
            return "card_back.png"

        value = card_code[:-1]
        suit = card_code[-1]

        suit_name = suit_map.get(suit)
        if suit_name is None:
            return "card_back.png"

        value = value_map.get(value, value)


        if str(value).isdigit() and int(value) < 10:
            value = f"0{int(value)}"

        return f"card_{suit_name}_{value}.png"

    def get_card_image(self, card, max_width=120, max_height=170, min_zoom=1):
        if not hasattr(self, "card_image_cache"):
            self.card_image_cache = {}

        filename = self.card_code_to_filename(card)
        key = (filename, max_width, max_height, min_zoom)

        if key in self.card_image_cache:
            return self.card_image_cache[key]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        cards_dir = os.path.join(base_dir, "assets", "cards", "medium")
        path = os.path.join(cards_dir, filename)

        if not os.path.exists(path):
            print("[BRAK PLIKU KARTY]", path, "dla karty:", card)
            path = os.path.join(cards_dir, "card_back.png")

        if not os.path.exists(path):
            print("[BRAK card_back.png] Sprawdź folder:", cards_dir)
            return None

        try:
            photo = tk.PhotoImage(file=path)
        except tk.TclError as error:
            print("[BŁĄD OBRAZKA]", path, error)
            return None


        if photo.width() > 0 and photo.height() > 0:
            possible_zoom = min(max_width // photo.width(), max_height // photo.height())
            zoom_factor = max(1, min_zoom, possible_zoom)
            if zoom_factor > 1:
                photo = photo.zoom(zoom_factor, zoom_factor)


        scale_x = max(1, (photo.width() + max_width - 1) // max_width)
        scale_y = max(1, (photo.height() + max_height - 1) // max_height)
        scale = max(scale_x, scale_y)

        if scale > 1:
            photo = photo.subsample(scale, scale)

        self.card_image_cache[key] = photo
        return photo

    def make_card_label(self, parent, card_text="—", command=None, selected=False, width=5, height=3):
        parent_bg = parent.cget("bg") if hasattr(parent, "cget") else "#123F32"
        border = 5 if selected else 2
        highlight = "#F4D35E" if selected else parent_bg


        if width <= 4 or height <= 2:
            max_width, max_height, min_zoom = 84, 120, 1
        else:
            max_width, max_height, min_zoom = 140, 200, 2

        photo = self.get_card_image(card_text, max_width=max_width, max_height=max_height, min_zoom=min_zoom)

        if photo is not None:
            if command:
                lbl = tk.Button(
                    parent,
                    image=photo,
                    bg=highlight,
                    activebackground="#E9C46A",
                    relief="raised",
                    bd=border,
                    command=command,
                    cursor="hand2",
                )
            else:
                lbl = tk.Label(
                    parent,
                    image=photo,
                    bg=highlight,
                    relief="raised",
                    bd=border,
                )


            lbl.image = photo
            lbl.pack(side="left", padx=6, pady=6)
            return lbl


        card_text = self.normalize_card(card_text)
        suit = str(card_text)[-1:] if card_text else ""
        is_red = suit in ["♥", "♦"]
        fg = "#C1121F" if is_red else "#1D1D1D"
        bg = "#FFF7E6" if selected else "#F8F7F2"

        if command:
            lbl = tk.Button(
                parent,
                text=card_text,
                width=width,
                height=height,
                bg=bg,
                fg=fg,
                font=("Arial", 20, "bold"),
                relief="raised",
                bd=border,
                command=command,
                cursor="hand2",
            )
        else:
            lbl = tk.Label(
                parent,
                text=card_text,
                width=width,
                height=height,
                bg=bg,
                fg=fg,
                font=("Arial", 20, "bold"),
                relief="raised",
                bd=border,
            )

        lbl.pack(side="left", padx=6, pady=6)
        return lbl

    def normalize_card(self, card):
        code = self.normalize_card_code_for_image(card)
        if code == "BACK":
            return "—"

        face = code[:-1]
        suit = code[-1]
        face_map = {"T": "10"}
        suit_map = {"H": "♥", "D": "♦", "C": "♣", "S": "♠"}

        if suit in suit_map:
            return f"{face_map.get(face, face)}{suit_map[suit]}"
        return str(card)

    def parse_card(self, card):
        code = self.normalize_card_code_for_image(card)
        if code == "BACK" or len(code) < 2:
            return None, None
        return code[:-1], code[-1]

    def format_effect(self, effect):
        effect = effect or {}
        name = effect.get("name")
        if name is None:
            return "Efekt: brak"
        if name in ["DRAW", "BLOCK"]:
            return f"Efekt: {name}, siła: {effect.get('severity')}"
        if name == "DEMAND SUIT":
            return f"Efekt: DEMAND SUIT, kolor: {effect.get('suit')}"
        if name == "DEMAND FACE":
            return f"Efekt: DEMAND FACE, wartość: {effect.get('face')}"
        return f"Efekt: {name}"

    def log(self, text):
        print(text)
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def make_log_panel(self, parent, title="LOG GRY"):
        log_panel = self.make_panel(parent, bg="#123F32")
        tk.Label(
            log_panel,
            text=title,
            font=("Arial", 15, "bold"),
            fg="#F8F7F2",
            bg="#123F32",
        ).pack(anchor="w")

        self.log_text = tk.Text(
            log_panel,
            width=32,
            height= 4,
            bg="#09251D",
            fg="#F8F7F2",
            insertbackground="#F8F7F2",
            font=("Consolas", 10),
            relief="flat",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text.configure(state="disabled")
        return log_panel





    def get_connection_candidates(self):
        manual = self.server_var.get().strip()
        host_ip = get_local_ip()



        return unique_list(["127.0.0.1", "localhost", manual, DEFAULT_SERVER, host_ip])

    def connect_to_server(self, show_errors=True):
        if self.connected:
            self.status_var.set(f"Połączono z serwerem: {self.connected_server}:{PORT}")
            return True

        errors = []
        for server in self.get_connection_candidates():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect((server, PORT))
                sock.settimeout(None)

                self.client = sock
                self.connected = True
                self.connected_server = server
                self.status_var.set(f"Połączono z serwerem: {server}:{PORT}")
                self.log(f"[SYSTEM] Połączono z serwerem {server}:{PORT}")

                self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
                self.receive_thread.start()
                return True
            except OSError as error:
                errors.append(f"{server}: {error}")

        self.connected = False
        self.connected_server = None
        self.status_var.set("Brak połączenia z serwerem")
        self.log("[BŁĄD] Nie udało się połączyć z serwerem.")
        for error in errors:
            self.log("  " + error)

        if show_errors:
            messagebox.showerror(
                "Brak serwera",
                "Nie mogę połączyć się z serwerem.\n"
                "Sprawdź, czy host_gui.py działa i czy adres/port są takie same."
            )
        return False

    def send(self, msg):
        if not self.connected or self.client is None:
            messagebox.showwarning("Brak połączenia", "Najpierw uruchom host_gui.py i połącz klienta.")
            return False

        try:
            msg_str = json.dumps(msg)
            message = msg_str.encode(FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b" " * (HEADER - len(send_length))

            self.client.sendall(send_length)
            self.client.sendall(message)
            return True
        except OSError as error:
            self.connected = False
            self.status_var.set("Utracono połączenie z serwerem")
            self.log(f"[BŁĄD] Nie udało się wysłać wiadomości: {error}")
            return False

    def receive_loop(self):
        while self.running:
            try:
                header = recv_exact(self.client, HEADER)
                if header is None:
                    break

                msg_length_text = header.decode(FORMAT).strip()
                if not msg_length_text:
                    continue

                msg_length = int(msg_length_text)
                payload = recv_exact(self.client, msg_length)
                if payload is None:
                    break

                msg = json.loads(payload.decode(FORMAT))
                self.root.after(0, self.handle_server_msg, msg)

            except (OSError, ValueError, json.JSONDecodeError) as error:
                if self.running:
                    self.root.after(0, self.log, f"[BŁĄD ODBIORU] {error}")
                break

        self.connected = False
        if self.running:
            self.root.after(0, self.status_var.set, "Rozłączono z serwerem")





    def change_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor tła", initialcolor=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.root.configure(bg=self.bg_color)

            if self.active_game == "POKER":
                self.show_poker()
            elif self.active_game == "MAKAO":
                self.show_makao()
            else:
                self.show_menu()

    def show_rules_poker(self):
        rules = (
            "Każdy gracz otrzymuje dwie karty własne\n"
            "Na stole w różnych fazach gry pokazuje się łącznie 5 kart współnych (preflop, flop, turn, river)\n"
            "Celem jest stworzenie najlepszego układu pięciokartowego\n"
            "CALL - wyrównanie puli, RAISE - podbicie puli, FOLD - spasowanie\n"
            "Na początku każdej rundy wyznaczana jest osoba, która musi rozpocząć pierwszą licytację od najmnieszego betu w preflopie."
            )
        messagebox.showinfo("Zasady: Poker", rules)

    def show_rules_makao(self):
        rules = (
            "Polega na dopasowaniu karty kolorem lub figurą\n"
            "Karty funkcyjne:\n"
            "   - 2, 3: Następny gracz dobiera karty (2 lub 3).\n"
            "   - 4: Następny gracz czeka kolejkę.\n"
            "   - Walet (J): Żądanie wartości karty.\n"
            "   - As (A): Żądanie koloru karty.\n"
            "   - Król (K): Specjalne efekty (dobieranie dla innych).\n"
            "Celem jest pozbycie się wszystkich kart\n"
            "W przypadku posiadania jednej karty należy wcisnąć 'makao', jeśli ktoś wyprzedzi, wówczas ta osoba pobiera trzy karty."
            )
        messagebox.showinfo("Zasady: Makao", rules)

    def show_history_window(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Historia rozegranych gier")
        history_window.geometry("700x500")
        history_window.configure(bg="#123F32")

        tk.Label(
            history_window,
            text="HISTORIA GIER",
            font=("Arial", 18, "bold"),
            fg="#F8F7F2",
            bg="#123F32"
        ).pack(pady=12)

        text_widget = tk.Text(
            history_window,
            bg="#09251D",
            fg="#F8F7F2",
            font=("Consolas", 11),
            wrap="word"
        )

        text_widget.pack(fill="both", expand=True, padx=15, pady=15)

        history_lines = self.stats.load_history()

        if not history_lines:
            text_widget.insert("end", "Brak zapisanych gier.")
        else:
            for line in reversed(history_lines):
                text_widget.insert("end", line)

        text_widget.configure(state="disabled")


    def show_menu(self):
        self.refresh_menu_stats()

        self.active_game = None
        self.clear_window()
        self.root.configure(bg=self.bg_color)

        outer = self.make_screen(padx=0, pady=0)

        self.make_title(outer, "SYMULATOR KART", size=40).pack(pady=(self.scaled(45), 8))

        rules_frame = tk.Frame(outer, bg=self.bg_color)
        rules_frame.pack(pady=10)

        self.make_button(rules_frame, "ZASADY POKERA", self.show_rules_poker, bg="#3D5A80", fg="white", width=20).grid(row=0, column=0, padx=10)
        self.make_button(rules_frame, "ZASADY MAKAO", self.show_rules_makao, bg="#3D5A80", fg="white", width=20).grid(row=0, column=1, padx=10)

        self.make_button(outer, "Zmień kolor tła", self.change_color, bg="#F8F7F2", width=20).pack(pady=10)
        self.make_button(outer, "HISTORIA GIER", self.show_history_window, bg="#F4A261", width=20).pack(pady=10)

        tk.Label(
            outer,
            text="Wybierz grę i dołącz do stołu",
            font=("Arial", 16),
            fg="#DDE7DD",
            bg=self.bg_color,
        ).pack(pady=(0, 25))

        card = self.make_panel(outer, bg="#123F32", padx=45, pady=32)
        card.pack()

        tk.Label(
            card,
            text="Adres serwera:",
            font=("Arial", 12, "bold"),
            fg="#F8F7F2",
            bg="#123F32",
        ).grid(row=0, column=0, sticky="e", padx=(0, 8), pady=(0, 18))

        server_entry = tk.Entry(card, textvariable=self.server_var, font=("Arial", 13), width=22, justify="center")
        server_entry.grid(row=0, column=1, columnspan=2, sticky="w", pady=(0, 18))

        poker_btn = self.make_button(card, "POKER", lambda: self.join_game("POKER"), bg="#E9C46A")
        poker_btn.grid(row=1, column=0, padx=14, pady=12)

        makao_btn = self.make_button(card, "MAKAO", lambda: self.join_game("MAKAO"), bg="#A7C957")
        makao_btn.grid(row=1, column=1, padx=14, pady=12)

        reconnect_btn = self.make_button(card, "POŁĄCZ PONOWNIE", lambda: self.connect_to_server(show_errors=True), bg="#F8F7F2", width=20)
        reconnect_btn.grid(row=2, column=0, columnspan=2, pady=(18, 0))

        stats_panel = self.make_panel(outer, bg="#123F32", padx=22, pady=18)
        stats_panel.pack(pady=18)

        tk.Label(
            stats_panel,
            text="STATYSTYKI",
            font=("Arial", 15, "bold"),
            fg="#F8F7F2",
            bg="#123F32",
        ).pack(anchor="w")

        tk.Label(
            stats_panel,
            textvariable=self.menu_stats_var,
            font=("Consolas", 12),
            fg="#F8F7F2",
            bg="#123F32",
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            outer,
            textvariable=self.status_var,
            font=("Arial", 12),
            fg="#DDE7DD",
            bg=self.bg_color,
        ).pack(pady=22)

    def join_game(self, target_game):
        if not self.connected:
            if not self.connect_to_server(show_errors=True):
                return

        join_msg = create_msg(
            game="SYSTEM",
            msg_type="JOIN",
            data={"target_game": target_game},
        )
        if not self.send(join_msg):
            return

        if target_game == "POKER":
            self.show_poker()
            self.log("[SYSTEM] Wysłano JOIN do POKERA. Gdy gracze dołączą, w panelu host_gui kliknij START POKER")
        elif target_game == "MAKAO":
            self.show_makao()
            self.log("[SYSTEM] Wysłano JOIN do MAKAO. Gdy gracze dołączą, w panelu host_gui kliknij START MAKAO")





    def show_poker(self):
        self.active_game = "POKER"
        self.clear_window()

        main = self.make_screen(padx=24, pady=18)

        top = tk.Frame(main, bg=self.bg_color)
        top.pack(fill="x")
        self.make_title(top, "POKER TEXAS HOLD'EM", size=27).pack(side="left")
        self.make_button(top, "MENU", self.show_menu, bg="#F8F7F2", width=10).pack(side="right")

        tk.Label(main, textvariable=self.status_var, font=("Arial", 12), fg="#DDE7DD", bg=self.bg_color).pack(anchor="w", pady=(3, 10))

        table_panel = self.make_panel(main, bg="#155846", padx=18, pady=14)
        table_panel.pack(fill="x", pady=(0, 14))
        tk.Label(table_panel, text="STÓŁ POKERA", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#155846").pack(anchor="w")

        self.poker_table_canvas = tk.Canvas(
            table_panel,
            height=self.scaled(255),
            bg="#155846",
            highlightthickness=0,
            bd=0,
        )
        self.poker_table_canvas.pack(fill="x", expand=True, pady=(7, 0))
        self.poker_table_canvas.bind("<Configure>", lambda event: self.draw_poker_table())



        self.poker_community_frame = None
        self.draw_poker_table()

        stats = tk.Frame(main, bg=self.bg_color)
        stats.pack(fill="x", pady=(0, 14))
        for i, var in enumerate([
            self.poker_player_var,
            self.poker_phase_var,
            self.poker_pot_var,
            self.poker_current_bet_var,
            self.poker_your_bet_var,
            self.poker_folded_var,
        ]):
            box = self.make_panel(stats, bg="#123F32", padx=12, pady=10)
            box.grid(row=0, column=i, padx=4, sticky="nsew")
            stats.columnconfigure(i, weight=1)
            tk.Label(box, textvariable=var, font=("Arial", 11, "bold"), fg="#F8F7F2", bg="#123F32", wraplength=165, justify="center").pack()

        bottom = tk.Frame(main, bg=self.bg_color)
        bottom.pack(fill="both", expand=True)
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=2)
        bottom.rowconfigure(0, weight=1)

        hand_panel = self.make_panel(bottom, bg="#123F32")
        hand_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(hand_panel, text="TWOJE KARTY", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#123F32").pack(anchor="w")
        self.poker_hand_frame = tk.Frame(hand_panel, bg="#123F32")
        self.poker_hand_frame.pack(pady=self.scaled(14))
        self.set_poker_cards(self.poker_hand_frame, self.poker_hand_cards, placeholders=2)

        tk.Label(hand_panel, textvariable=self.poker_chips_var, font=("Arial", 16, "bold"), fg="#F4D35E", bg="#123F32").pack(pady=(0, 10))

        action_panel = self.make_panel(bottom, bg="#123F32")
        action_panel.grid(row=0, column=1, sticky="nsew", padx=8)

        self.poker_call_button = self.make_button(action_panel, "CALL", self.send_poker_call, bg="#A7C957", width=12)
        self.poker_call_button.pack(fill="x", pady=6)
        self.poker_fold_button = self.make_button(action_panel, "FOLD", self.send_poker_fold, bg="#E76F51", fg="#FFFFFF", width=12)
        self.poker_fold_button.pack(fill="x", pady=6)

        tk.Label(action_panel, text="Raise do kwoty:", font=("Arial", 11), fg="#DDE7DD", bg="#123F32").pack(anchor="w", pady=(15, 4))
        self.poker_raise_entry = tk.Entry(action_panel, font=("Arial", 15), justify="center")
        self.poker_raise_entry.pack(fill="x", pady=(0, 8))
        self.poker_raise_entry.insert(0, "30")
        self.poker_raise_button = self.make_button(action_panel, "RAISE", self.send_poker_raise, bg="#E9C46A", width=12)
        self.poker_raise_button.pack(fill="x", pady=6)
        self.set_poker_action_buttons(False)

        log_panel = self.make_log_panel(bottom)
        log_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        chat_frame = tk.Frame(log_panel, bg="#123F32")
        chat_frame.pack(fill="x", side="bottom", pady=(5, 0))

        self.chat_entry = tk.Entry(chat_frame, font=("Arial", 12))
        self.chat_entry.pack(side="left", fill="x", expand=True)

        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())

        chat_btn = self.make_button(chat_frame, "WYŚLIJ", self.send_chat_message, bg="#A7C957", width=8)
        chat_btn.pack(side="right", padx=(5, 0))

        self.refresh_poker_labels()

    def short_card_text(self, card):
        code = self.normalize_card_code_for_image(card)
        if code == "BACK":
            return "—"
        value = code[:-1].replace("T", "10")
        suit = code[-1]
        suit_symbols = {
            "H": "♥",
            "D": "♦",
            "C": "♣",
            "S": "♠",
        }
        return value + suit_symbols.get(suit, suit)

    def draw_poker_table(self):
        canvas = self.poker_table_canvas
        if canvas is None:
            return

        canvas.delete("all")
        width = max(canvas.winfo_width(), 720)
        height = max(canvas.winfo_height(), 240)
        cx = width / 2
        cy = height / 2 + 8


        canvas.create_oval(
            110, 32,
            width - 110, height - 32,
            fill="#0F6B52",
            outline="#E9C46A",
            width=3,
        )
        canvas.create_oval(
            145, 58,
            width - 145, height - 58,
            fill="#155846",
            outline="#2A6F5A",
            width=2,
        )

        canvas.create_text(
            cx,
            cy - 72,
            text=f"Pula: {self.poker_pot}   |   Bet: {self.poker_current_bet}",
            fill="#F8F7F2",
            font=("Arial", 12, "bold"),
        )


        card_w = 58
        card_h = 74
        gap = 8
        cards = list(self.poker_community_cards or [])
        total = 5 * card_w + 4 * gap
        start_x = cx - total / 2
        y1 = cy - card_h / 2 - 4

        for i in range(5):
            x1 = start_x + i * (card_w + gap)
            x2 = x1 + card_w
            y2 = y1 + card_h
            text = self.short_card_text(cards[i]) if i < len(cards) else "—"
            canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#F8F7F2" if text != "—" else "#0B3D2E",
                outline="#E9C46A" if text != "—" else "#2A6F5A",
                width=2,
            )
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=text,
                fill="#10231D" if text != "—" else "#DDE7DD",
                font=("Arial", 13, "bold"),
            )

        players = list(self.poker_players or [])
        if not players and self.my_player_id is not None:
            players = [{
                "player_id": self.my_player_id,
                "is_bot": False,
                "chips": "-",
                "bet": self.poker_your_bet,
                "folded": False,
                "all_in": False,
            }]

        if self.my_player_id is not None:
            my_index = None
            for index, player in enumerate(players):
                pid = player.get("player_id")
                if pid == self.my_player_id or str(pid) == str(self.my_player_id):
                    my_index = index
                    break
            if my_index is not None:
                players = players[my_index:] + players[:my_index]

        count = len(players)
        if count == 0:
            canvas.create_text(
                cx,
                height - 38,
                text="Czekam na dane o graczach...",
                fill="#DDE7DD",
                font=("Arial", 11),
            )
            return


        seat_w = 136 if count <= 6 else 112 if count <= 8 else 96
        seat_h = 58 if count <= 8 else 50
        font_main = 10 if count <= 8 else 9
        font_sub = 8 if count <= 8 else 7
        rx = max(230, width / 2 - seat_w / 2 - 24)
        ry = max(88, height / 2 - seat_h / 2 - 12)


        start_angle = math.pi / 2

        for index, player in enumerate(players):
            angle = start_angle + (2 * math.pi * index / count)
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)

            pid = player.get("player_id")
            is_me = pid == self.my_player_id or str(pid) == str(self.my_player_id)
            is_turn = pid == self.poker_turn_player or str(pid) == str(self.poker_turn_player)
            is_blind = pid == self.poker_blind_player or str(pid) == str(self.poker_blind_player)
            is_folded = bool(player.get("folded"))
            is_all_in = bool(player.get("all_in"))
            is_bot = bool(player.get("is_bot"))

            fill = "#123F32"
            outline = "#2A6F5A"
            label_color = "#F8F7F2"

            if is_folded:
                fill = "#5A2720"
                outline = "#E76F51"
            elif is_turn:
                fill = "#A7C957"
                outline = "#F4D35E"
                label_color = "#10231D"
            elif is_me:
                fill = "#E9C46A"
                outline = "#F8F7F2"
                label_color = "#10231D"
            elif is_all_in:
                fill = "#3D5A80"
                outline = "#F8F7F2"

            x1 = x - seat_w / 2
            y1 = y - seat_h / 2
            x2 = x + seat_w / 2
            y2 = y + seat_h / 2

            canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)

            badges = []
            if is_me:
                badges.append("TY")
            if is_bot:
                badges.append("BOT")
            if is_blind:
                badges.append("BLIND")
            if is_all_in:
                badges.append("ALL-IN")
            if is_folded:
                badges.append("FOLD")

            title = f"Gracz {pid}"
            if badges:
                title += "  " + "/".join(badges)

            chips = player.get("chips", "-")
            bet = player.get("bet", 0)

            canvas.create_text(
                x,
                y - 13,
                text=title,
                fill=label_color,
                font=("Arial", font_main, "bold"),
            )
            canvas.create_text(
                x,
                y + 10,
                text=f"żetony: {chips} | wkład: {bet}",
                fill=label_color,
                font=("Arial", font_sub),
            )

    def set_poker_cards(self, frame, cards, placeholders=0):
        if frame is None:
            return
        for widget in frame.winfo_children():
            widget.destroy()
        for card in cards:
            self.make_card_label(frame, card)
        for _ in range(max(0, placeholders - len(cards))):
            self.make_card_label(frame, "—")

    def set_poker_action_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for button in [self.poker_call_button, self.poker_fold_button, self.poker_raise_button]:
            if button is not None:
                button.configure(state=state)
        if self.poker_raise_entry is not None:
            self.poker_raise_entry.configure(state=state)

    def send_poker_move(self, move_data):
        if self.my_player_id is None:
            messagebox.showwarning("Brak ID gracza", "Serwer nie wysłał jeszcze Twojego numeru gracza.")
            return

        msg = create_msg("POKER", "MOVE", player_id=self.my_player_id, data=move_data)
        if self.send(msg):
            self.set_poker_action_buttons(False)
            self.status_var.set("Ruch wysłany. Czekasz na pozostałych graczy...")
            self.log(f"[TY/POKER] {move_data}")

    def send_poker_call(self):
        self.send_poker_move({"action": "CALL"})

    def send_poker_fold(self):
        self.send_poker_move({"action": "FOLD"})

    def send_poker_raise(self):
        value = self.poker_raise_entry.get().strip() if self.poker_raise_entry else ""
        try:
            amount = int(value)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Zła kwota", "Wpisz dodatnią liczbę, np. 30.")
            return
        self.send_poker_move({"action": "RAISE", "amount": amount})

    def refresh_poker_labels(self):
        self.poker_player_var.set(f"Gracz: {self.my_player_id if self.my_player_id is not None else '-'}")
        self.poker_phase_var.set(f"Faza: {self.poker_phase}")
        self.poker_pot_var.set(f"Pula: {self.poker_pot}")
        self.poker_current_bet_var.set(f"Aktualny bet: {self.poker_current_bet}")
        self.poker_your_bet_var.set(f"Twój wkład: {self.poker_your_bet}")
        folded = ", ".join(str(p) for p in self.poker_folded_players) if self.poker_folded_players else "-"
        self.poker_folded_var.set(f"Spasowani: {folded}")





    def send_chat_message(self):
        text = self.chat_entry.get().strip()
        if text:
            msg = {
                "game": "POKER",
                "type": "CHAT",
                "player_id": self.my_player_id,
                "chat": text
            }
            self.send(msg)
            self.chat_entry.delete(0, tk.END)





    def show_makao(self):
        self.active_game = "MAKAO"
        self.clear_window()

        main = self.make_screen(padx=24, pady=18)

        top = tk.Frame(main, bg=self.bg_color)
        top.pack(fill="x")
        self.make_title(top, "MAKAO", size=30).pack(side="left")
        self.make_button(top, "MENU", self.show_menu, bg="#F8F7F2", width=10).pack(side="right")

        tk.Label(main, textvariable=self.status_var, font=("Arial", 12), fg="#DDE7DD", bg=self.bg_color).pack(anchor="w", pady=(3, 10))

        top_info = tk.Frame(main, bg=self.bg_color)
        top_info.pack(fill="x", pady=(0, 12))
        top_info.columnconfigure(0, weight=1)
        top_info.columnconfigure(1, weight=1)
        top_info.columnconfigure(2, weight=1)

        table_panel = self.make_panel(top_info, bg="#155846", padx=20, pady=16)
        table_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(table_panel, text="STÓŁ", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#155846").pack(anchor="w")
        self.makao_table_card_frame = tk.Frame(table_panel, bg="#155846")
        self.makao_table_card_frame.pack(anchor="w", pady=(10, 6))
        self.refresh_makao_table_card()
        self.make_small_label(table_panel, textvariable=self.makao_table_var, bg="#155846", size=13, bold=True).pack(anchor="w", pady=(4, 4))
        self.make_small_label(table_panel, textvariable=self.makao_turn_var, bg="#155846", size=12).pack(anchor="w", pady=3)
        self.make_small_label(table_panel, textvariable=self.makao_effect_var, bg="#155846", size=12).pack(anchor="w", pady=3)

        turn_panel = self.make_panel(top_info, bg="#123F32", padx=20, pady=16)
        turn_panel.grid(row=0, column=1, sticky="nsew", padx=8)
        tk.Label(turn_panel, text="TWOJA TURA", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#123F32").pack(anchor="w")
        self.make_small_label(turn_panel, textvariable=self.makao_player_var, bg="#123F32", size=12).pack(anchor="w", pady=(10, 3))
        self.make_small_label(turn_panel, textvariable=self.makao_played_var, bg="#123F32", size=12).pack(anchor="w", pady=3)
        self.make_small_label(turn_panel, textvariable=self.makao_drawn_var, bg="#123F32", size=12).pack(anchor="w", pady=3)

        players_panel = self.make_panel(top_info, bg="#123F32", padx=20, pady=16)
        players_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        tk.Label(players_panel, text="GRACZE", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#123F32").pack(anchor="w")
        self.makao_players_frame = tk.Frame(players_panel, bg="#123F32")
        self.makao_players_frame.pack(fill="both", expand=True, pady=(8, 0))
        tk.Label(
            players_panel,
            text="Zgłoś brak MAKAO:",
            fg="#F8F7F2",
            bg="#123F32",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(10, 2))

        report_frame = tk.Frame(players_panel, bg="#123F32")
        report_frame.pack(fill="x", pady=6)

        self.makao_report_menu = tk.OptionMenu(
            report_frame,
            self.makao_report_target,
            ""
        )
        self.makao_report_menu.configure(font=("Arial", 10))
        self.makao_report_menu.pack(side="left", fill="x", expand=True)

        self.make_button(
            report_frame,
            "ZGŁOŚ",
            self.send_makao_report,
            bg="#E76F51",
            width=10
        ).pack(side="left", padx=(6, 0))

        middle = tk.Frame(main, bg=self.bg_color)
        middle.pack(fill="both", expand=True)
        middle.columnconfigure(0, weight=5)
        middle.columnconfigure(1, weight=3)
        middle.columnconfigure(2, weight=2)
        middle.rowconfigure(0, weight=1)

        hand_panel = self.make_panel(middle, bg="#123F32")
        hand_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(hand_panel, text="TWOJE KARTY — kliknij kartę, żeby ją wybrać", font=("Arial", 15, "bold"), fg="#F8F7F2", bg="#123F32").pack(anchor="w")
        self.makao_hand_frame = tk.Frame(hand_panel, bg="#123F32")
        self.makao_hand_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.refresh_makao_hand()

        action_panel = self.make_panel(middle, bg="#123F32")
        action_panel.grid(row=0, column=1, sticky="nsew", padx=8)
        action_panel.columnconfigure(0, weight=1)
        action_panel.columnconfigure(1, weight=1)

        tk.Label(action_panel,text="RUCH",font=("Arial", 15, "bold"),fg="#F8F7F2",bg="#123F32").grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.make_small_label(action_panel,textvariable=self.makao_selected_card_var,bg="#123F32",size=12,bold=True).grid(row=1, column=0, sticky="w", pady=(0, 10))

        tk.Label(action_panel,text="J → wartość",font=("Arial", 10),fg="#DDE7DD",bg="#123F32").grid(row=2, column=0, sticky="w", padx=4)

        tk.Label(action_panel,text="A → kolor",font=("Arial", 10),fg="#DDE7DD",bg="#123F32").grid(row=2, column=1, sticky="w", padx=4)

        face_menu = tk.OptionMenu(action_panel,self.face_demand_var,"5", "6", "7", "8", "9", "T", "Q")

        face_menu.configure(font=("Arial", 11),bg="#F8F7F2",relief="flat")

        face_menu.grid(row=3,column=0,sticky="ew",padx=4,pady=(2, 14))

        suit_menu = tk.OptionMenu(action_panel,self.suit_demand_var,"C", "D", "H", "S")

        suit_menu.configure(font=("Arial", 11),bg="#F8F7F2",relief="flat")

        suit_menu.grid(row=3,column=1,sticky="ew",padx=4,pady=(2, 14))

        self.makao_play_button = self.make_button(action_panel,"ZAGRAJ KARTĘ",self.send_makao_play,bg="#A7C957",width=14)

        self.makao_play_button.grid(row=6,column=0,sticky="ew",padx=4,pady=4)

        self.makao_draw_button = self.make_button(action_panel,"DOBIERZ",self.send_makao_draw,bg="#E9C46A",width=14)

        self.makao_draw_button.grid(row=6,column=1,sticky="ew",padx=4,pady=4)

        self.makao_end_button = self.make_button(action_panel,"KONIEC TURY",self.send_makao_end_turn,bg="#E76F51",fg="#FFFFFF",width=14)

        self.makao_end_button.grid(row=7,column=0,sticky="ew",padx=4, pady=4)

        self.makao_makao_button = self.make_button(action_panel,"MAKAO",self.send_makao_makao,bg="#49B543",width=14)

        self.makao_makao_button.grid(row=7,column=1,sticky="ew",padx=4,pady=4)

        self.set_makao_action_buttons(False)

        log_panel = self.make_log_panel(middle)
        log_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        chat_frame = tk.Frame(log_panel, bg="#123F32")
        chat_frame.pack(fill="x", side="bottom", pady=(5, 0))

        self.chat_entry = tk.Entry(chat_frame, font=("Arial", 12))
        self.chat_entry.pack(side="left", fill="x", expand=True)

        self.chat_entry.bind("<Return>", lambda e: self.send_chat_message())

        chat_btn = self.make_button(chat_frame, "WYŚLIJ", self.send_chat_message, bg="#A7C957", width=8)
        chat_btn.pack(side="right", padx=(5, 0))

        self.refresh_makao_labels()
        self.refresh_makao_players()

    def refresh_makao_table_card(self):
        if self.makao_table_card_frame is None:
            return

        for widget in self.makao_table_card_frame.winfo_children():
            widget.destroy()

        self.make_card_label(
            self.makao_table_card_frame,
            self.makao_table_card if self.makao_table_card else "BACK",
            width=5,
            height=3
        )

    def refresh_makao_hand(self):
        if self.makao_hand_frame is None:
            return
        for widget in self.makao_hand_frame.winfo_children():
            widget.destroy()

        if not self.makao_hand_cards:
            tk.Label(
                self.makao_hand_frame,
                text="Czekam na karty od serwera...",
                fg="#DDE7DD",
                bg="#123F32",
                font=("Arial", 13),
            ).pack(anchor="w", pady=12)
            return


        row = None
        for index, card in enumerate(self.makao_hand_cards):
            if index % 8 == 0:
                row = tk.Frame(self.makao_hand_frame, bg="#123F32")
                row.pack(fill="x", anchor="w")
            selected = str(card) == str(self.selected_makao_card)
            self.make_card_label(row, card, command=lambda c=card: self.select_makao_card(c), selected=selected, width=4, height=2)

    def select_makao_card(self, card):
        self.selected_makao_card = card
        self.makao_selected_card_var.set(f"Wybrana karta: {self.normalize_card(card)}")
        self.refresh_makao_hand()

    def refresh_makao_players(self):
        if self.makao_players_frame is None:
            return
        for widget in self.makao_players_frame.winfo_children():
            widget.destroy()

        if not self.makao_players:
            tk.Label(self.makao_players_frame, text="Brak danych", fg="#DDE7DD", bg="#123F32", font=("Arial", 11)).pack(anchor="w")
            return

        for player in self.makao_players:
            player_id = player.get("player_id")
            cards_count = player.get("cards_count")
            blocked = player.get("blocked")
            said_makao = player.get("makao", False)
            prefix = "➜ " if player_id == self.makao_turn_player else "   "
            text = f"{prefix}Gracz {player_id}: kart {cards_count}, blok {blocked}"
            if said_makao:
                text+=", MAKAO"
            tk.Label(self.makao_players_frame, text=text, fg="#F8F7F2", bg="#123F32", font=("Arial", 11), anchor="w").pack(anchor="w", pady=2)

        menu = self.makao_report_menu["menu"]
        menu.delete(0, "end")

        for player in self.makao_players:
            pid = player["player_id"]

            menu.add_command(
                label=f"Gracz {pid}",
                command=lambda p=pid: self.makao_report_target.set(p)
            )


        if self.makao_players and not self.makao_report_target.get():
            self.makao_report_target.set(self.makao_players[0]["player_id"])

    def set_makao_action_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for button in [self.makao_play_button, self.makao_draw_button, self.makao_end_button]:
            if button is not None:
                button.configure(state=state)

    def refresh_makao_labels(self):
        self.makao_player_var.set(f"Gracz: {self.my_player_id if self.my_player_id is not None else '-'}")
        self.makao_turn_var.set(f"Tura: {self.makao_turn_player if self.makao_turn_player is not None else '-'}")
        self.makao_table_var.set(f"Karta na stole: {self.normalize_card(self.makao_table_card)}")
        self.makao_effect_var.set(self.format_effect(self.makao_effect))

        played = ", ".join(self.normalize_card(c) for c in self.makao_played_this_turn) if self.makao_played_this_turn else "-"
        drawn = ", ".join(self.normalize_card(c) for c in self.makao_drawn_this_turn) if self.makao_drawn_this_turn else "-"
        self.makao_played_var.set(f"Zagrane w tej turze: {played}")
        self.makao_drawn_var.set(f"Dobrane w tej turze: {drawn}")

        selected = self.normalize_card(self.selected_makao_card) if self.selected_makao_card is not None else "-"
        self.makao_selected_card_var.set(f"Wybrana karta: {selected}")

    def send_makao_play(self):
        if self.my_player_id is None:
            messagebox.showwarning("Brak ID gracza", "Serwer nie wysłał jeszcze Twojego numeru gracza.")
            return
        if self.selected_makao_card is None:
            messagebox.showwarning("Nie wybrano karty", "Kliknij kartę z ręki, którą chcesz zagrać.")
            return

        face, suit = self.parse_card(self.selected_makao_card)
        if not face or not suit:
            messagebox.showerror("Nie umiem odczytać karty", f"Karta ma dziwny format: {self.selected_makao_card}")
            return

        face_demand = None
        suit_demand = None
        if face == "J":
            face_demand = self.face_demand_var.get()
        elif face == "A":
            suit_demand = self.suit_demand_var.get()

        msg = create_msg(
            game="MAKAO",
            msg_type="PLAY",
            player_id=self.my_player_id,
            data={
                "face": face,
                "suit": suit,
                "face_demand": face_demand,
                "suit_demand": suit_demand,
            },
        )
        if self.send(msg):
            self.set_makao_action_buttons(False)
            self.log(f"[TY/MAKAO] PLAY {face}{suit}, face_demand={face_demand}, suit_demand={suit_demand}")
            self.status_var.set("Ruch wysłany. Czekam na odpowiedź serwera...")

    def send_makao_draw(self):
        if self.my_player_id is None:
            messagebox.showwarning("Brak ID gracza", "Serwer nie wysłał jeszcze Twojego numeru gracza.")
            return

        msg = create_msg("MAKAO", "DRAW", player_id=self.my_player_id)
        if self.send(msg):
            self.set_makao_action_buttons(False)
            self.log("[TY/MAKAO] DRAW")
            self.status_var.set("Dobieranie wysłane. Czekam na odpowiedź serwera...")

    def send_makao_end_turn(self):
        if self.my_player_id is None:
            messagebox.showwarning("Brak ID gracza", "Serwer nie wysłał jeszcze Twojego numeru gracza.")
            return

        msg = create_msg("MAKAO", "END TURN", player_id=self.my_player_id)
        if self.send(msg):
            self.set_makao_action_buttons(False)
            self.selected_makao_card = None
            self.refresh_makao_hand()
            self.refresh_makao_labels()
            self.log("[TY/MAKAO] END TURN")
            self.status_var.set("Koniec tury wysłany. Czekasz na pozostałych...")

    def send_makao_makao(self):
        if self.my_player_id is None:
            messagebox.showwarning("Brak ID gracza", "Serwer nie wysłał jeszcze Twojego numeru gracza.")
            return

        msg = create_msg("MAKAO", "MAKAO", player_id=self.my_player_id)
        if self.send(msg):
            self.refresh_makao_labels()
            self.refresh_makao_players()

    def send_makao_report(self):
        target = self.makao_report_target.get()

        if not target:
            messagebox.showwarning("Makao", "Wybierz gracza do zgłoszenia.")
            return

        msg = create_msg(
            game="MAKAO",
            msg_type="REPORT_MAKAO",
            player_id=self.my_player_id,
            data={
                "target": target
            }
        )

        if(self.send(msg)):
            self.log(f"[TY] Zgłoszono brak MAKAO: gracz {target}")
            self.refresh_makao_hand()
            self.refresh_makao_players()





    def handle_server_msg(self, msg):
        game = msg.get("game")
        if game == "POKER":
            self.handle_poker_msg(msg)
        elif game == "MAKAO":
            self.handle_makao_msg(msg)
        elif game == "SYSTEM":
            self.log(f"[SYSTEM] {msg}")
        else:
            self.log(f"[NIEZNANA WIADOMOŚĆ] {msg}")

    def handle_poker_msg(self, msg):
        msg_type = msg.get("type")
        data = msg.get("data", {}) or {}
        player_id = msg.get("player_id")
        chat = msg.get("chat")

        if msg_type == "HAND":
            self.my_player_id = player_id
            self.poker_hand_cards = data.get("cards", [])
            self.status_var.set("Dostałeś karty. Czekaj na swoją turę.")
            self.set_poker_cards(self.poker_hand_frame, self.poker_hand_cards, placeholders=2)
            self.refresh_poker_labels()
            self.draw_poker_table()
            self.log(f"[POKER] Twoje karty: {self.poker_hand_cards}")

        elif msg_type == "TABLE":
            self.poker_phase = data.get("phase", self.poker_phase)
            self.poker_pot = data.get("pot", self.poker_pot)
            self.poker_current_bet = data.get("current_bet", self.poker_current_bet)
            self.poker_community_cards = data.get("community_cards", self.poker_community_cards)
            self.poker_folded_players = data.get("folded_players", self.poker_folded_players)
            self.poker_players = data.get("players", self.poker_players)
            self.poker_turn_player = data.get("current_turn_player_id", self.poker_turn_player)
            self.poker_blind_player = data.get("blind_player_id", self.poker_blind_player)
            self.poker_round_bets = data.get("round_bets", self.poker_round_bets)

            chips_dict = data.get("chips", {})
            my_chips = chips_dict.get(str(self.my_player_id), chips_dict.get(self.my_player_id))
            if my_chips is not None:
                self.poker_chips_var.set(f"Żetony: {my_chips}")

            my_bet = self.poker_round_bets.get(str(self.my_player_id), self.poker_round_bets.get(self.my_player_id))
            if my_bet is not None:
                self.poker_your_bet = my_bet

            self.refresh_poker_labels()
            self.set_poker_cards(self.poker_community_frame, self.poker_community_cards, placeholders=5)
            self.draw_poker_table()
            self.log(f"[STÓŁ/POKER] faza={self.poker_phase}, pula={self.poker_pot}, bet={self.poker_current_bet}, tura={self.poker_turn_player}, karty={self.poker_community_cards}")

        elif msg_type == "TURN":
            self.poker_phase = data.get("phase", self.poker_phase)
            self.poker_community_cards = data.get("community_cards", self.poker_community_cards)
            self.poker_current_bet = data.get("current_bet", self.poker_current_bet)
            self.poker_your_bet = data.get("your_bet", self.poker_your_bet)
            self.poker_pot = data.get("pot", self.poker_pot)
            self.poker_turn_player = player_id

            self.refresh_poker_labels()
            self.set_poker_cards(self.poker_community_frame, self.poker_community_cards, placeholders=5)
            self.draw_poker_table()

            if player_id == self.my_player_id:
                self.status_var.set("Twoja kolej! Wybierz CALL, FOLD albo RAISE.")
                self.set_poker_action_buttons(True)
                self.log("[TURA/POKER] Teraz Twój ruch")
            else:
                self.status_var.set(f"Tura gracza {player_id}")
                self.set_poker_action_buttons(False)

        elif msg_type == "WINNER":
            winner = data.get("winner")
            pot = data.get("pot", self.poker_pot)

            if isinstance(winner, list):
                if self.my_player_id in winner:
                    split_pot = pot // len(winner)
                    self.stats.update_after_game("poker", split_pot, True)
            else:
                if winner == self.my_player_id:
                    self.stats.update_after_game("poker", pot, True)

            reason = data.get("reason")
            hand_name = data.get("hand_name")
            best_combo = data.get("best_combo")
            self.poker_community_cards = data.get("community_cards", self.poker_community_cards)
            self.set_poker_action_buttons(False)
            self.set_poker_cards(self.poker_community_frame, self.poker_community_cards, placeholders=5)
            self.draw_poker_table()

            winner_text = "Remis: " + ", ".join(str(w) for w in winner) if isinstance(winner, list) else f"Wygrał gracz {winner}"
            details = f"{winner_text}\nPula: {pot}\nPowód: {reason}"
            if hand_name:
                details += f"\nUkład: {hand_name}"
            if best_combo:
                details += f"\nNajlepsze karty: {best_combo}"

            self.status_var.set(winner_text)
            self.log("[KONIEC/POKER] " + details.replace("\n", " | "))
            messagebox.showinfo("Koniec rozdania", details)

        elif msg_type == "DEFEAT":
            self.stats.update_after_game("poker", 0, False)
            self.log("[PORAŻKA] Straciłeś wszystkie żetony!")
            messagebox.showinfo("Porażka", "Straciłeś wszystkie żetony. Odpadasz z gry.")
            self.show_menu()

        elif msg_type == "MOVE":
            action = data.get("action")
            amount = data.get("amount")
            amount_text = f" {amount}" if amount else ""
            self.log(f"[RUCH/POKER] Gracz {player_id}: {action}{amount_text}")

        elif msg_type == "CHAT":
            self.log(f"[CHAT] Gracz {player_id}: {chat}")

        elif msg_type == "ERROR":
            self.log(f"[ERROR/POKER] {data}")
            messagebox.showerror("Błąd z serwera", str(data))

        elif msg_type == "DISCONNECT":
            self.log(f"[INFO/POKER] Gracz {player_id} się rozłączył")

        else:
            self.log(f"[POKER] Nieznany typ wiadomości: {msg_type} | {msg}")

    def handle_makao_msg(self, msg):
        msg_type = msg.get("type")
        data = msg.get("data", {}) or {}
        player_id = msg.get("player_id")
        chat = msg.get("chat")

        if msg_type == "HAND":
            self.my_player_id = player_id
            self.makao_hand_cards = data.get("cards", [])
            self.selected_makao_card = None
            self.status_var.set("Dostałeś karty. Czekaj na swoją turę.")
            self.refresh_makao_labels()
            self.refresh_makao_hand()
            self.log(f"[MAKAO] Twoje karty: {self.makao_hand_cards}")

        elif msg_type == "MAKAO":
            self.log(f"[MAKAO] Gracz {player_id} powiedział Makao.")

        elif msg_type == "REPORT":
            self.log(f"[MAKAO] Gracz {player_id} został ukarany za brak Makao i dobrał 5 kart.")

        elif msg_type == "BLOCK":
            self.log(f"[MAKAO] Gracz {player_id} został pominięty przez blok. Czas: {data.get('duration')}")

        elif msg_type == "TABLE":
            self.makao_players = data.get("players", self.makao_players)
            self.makao_turn_player = data.get("turn", self.makao_turn_player)
            self.makao_played_this_turn = data.get("played", self.makao_played_this_turn)
            self.makao_table_card = data.get("table", self.makao_table_card)
            self.makao_effect = data.get("effect") or {}

            self.refresh_makao_labels()
            self.refresh_makao_table_card()
            self.refresh_makao_players()
            self.log(f"[STÓŁ/MAKAO] tura={self.makao_turn_player}, stół={self.makao_table_card}, efekt={self.makao_effect}")

        elif msg_type == "DRAW ERROR":
            self.log("[MAKAO] Wszystkie karty są w grze, dalsze dobieranie nie jest możliwe.")
            messagebox.showwarning("Makao", "Wszystkie karty są w grze, nie można dobrać kolejnych kart.")
            self.set_makao_action_buttons(True)

        elif msg_type == "EFFECT DRAW":
            self.log("[MAKAO] Aby pociągnąć karty z efektu albo poddać się blokowi, użyj KONIEC TURY.")
            messagebox.showinfo("Makao", "Przy aktywnym efekcie DRAW/BLOCK użyj przycisku KONIEC TURY.")
            self.set_makao_action_buttons(True)

        elif msg_type == "WINNER":
            winner = data.get("winner")
            if winner == self.my_player_id:
                self.stats.update_after_game("makao", 0, True)
            else:
                self.stats.update_after_game("makao", 0, False)

            self.set_makao_action_buttons(False)
            self.status_var.set(f"Wygrał gracz {winner}")
            self.log(f"[KONIEC/MAKAO] Wygrał gracz {winner}")
            messagebox.showinfo("Koniec gry", f"Wygrał gracz {winner}")

        elif msg_type == "TURN":
            if player_id != self.my_player_id:
                self.status_var.set(f"Tura gracza {player_id}")
                self.set_makao_action_buttons(False)
                return

            self.makao_hand_cards = data.get("hand", self.makao_hand_cards)
            self.makao_drawn_this_turn = data.get("drawn", [])
            self.makao_played_this_turn = data.get("played", [])
            self.makao_table_card = data.get("table", self.makao_table_card)
            self.makao_effect = data.get("effect") or {}
            self.makao_turn_player = self.my_player_id


            if self.selected_makao_card is not None and all(str(c) != str(self.selected_makao_card) for c in self.makao_hand_cards):
                self.selected_makao_card = None

            self.refresh_makao_labels()
            self.refresh_makao_table_card()
            self.refresh_makao_hand()
            self.refresh_makao_players()
            self.set_makao_action_buttons(True)
            self.status_var.set("Twoja kolej w Makao! Wybierz kartę, dobierz albo zakończ turę.")
            self.log("[TURA/MAKAO] Teraz Twój ruch")

        elif msg_type == "CHAT":
            self.log(f"[CHAT] Gracz {player_id}: {chat}")

        elif msg_type == "ERROR":
            self.log(f"[ERROR/MAKAO] {data}")
            messagebox.showerror("Błąd z serwera", str(data))
            self.set_makao_action_buttons(True)

        elif msg_type == "DISCONNECT":
            self.log(f"[INFO/MAKAO] Gracz {player_id} się rozłączył")

        else:
            self.log(f"[MAKAO] Nieznany typ wiadomości: {msg_type} | {msg}")





    def close_app(self):
        self.running = False
        try:
            if self.connected and self.client is not None:
                disconnect_msg = create_msg(
                    game=self.active_game or "SYSTEM",
                    msg_type="DISCONNECT",
                    player_id=self.my_player_id,
                )
                self.send(disconnect_msg)
        except Exception:
            pass

        try:
            if self.client is not None:
                self.client.close()
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CardGameClientApp(root)
    root.mainloop()
