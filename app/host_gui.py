import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox

from poker import PokerGame
from makao import MakaoGame

HEADER = 64
PORT = 5050
FORMAT = "utf-8"


def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"




BIND_HOST = "0.0.0.0"
DEFAULT_SERVER = get_local_ip()






def recv_exact(conn, length):
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data


def send_json(conn, msg):
    if conn is None:
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
        "chat": chat,
    }






class HostGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Poker / Makao - Host")


        self.bg_color = "#0B3D2E"
        self.panel_color = "#123F32"
        self.table_color = "#155846"
        self.dark_color = "#09251D"
        self.border_color = "#2A6F5A"
        self.text_color = "#F8F7F2"
        self.muted_color = "#DDE7DD"
        self.gold = "#E9C46A"
        self.green = "#A7C957"
        self.red = "#E76F51"
        self.blue = "#3D5A80"

        self.setup_window()
        self.root.configure(bg=self.bg_color)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.running = True
        self.server_socket = None
        self.accept_thread = None

        self.games = {
            "POKER": PokerGame(send_json, create_msg),
            "MAKAO": MakaoGame(send_json, create_msg),
        }

        self.server_status_var = tk.StringVar(value="Serwer nieuruchomiony")
        self.address_var = tk.StringVar(value=f"LAN: {DEFAULT_SERVER}:{PORT} | ten komputer: 127.0.0.1:{PORT}")

        self.poker_players_var = tk.StringVar(value="Gracze: 0")
        self.poker_bots_var = tk.StringVar(value="Boty: 0")
        self.poker_phase_var = tk.StringVar(value="Faza: waiting")
        self.poker_state_var = tk.StringVar(value="Pula: 0 | Bet: 0")
        self.poker_list_var = tk.StringVar(value="Brak graczy")

        self.makao_players_var = tk.StringVar(value="Gracze: 0")
        self.makao_bots_var = tk.StringVar(value="Boty: 0")
        self.makao_phase_var = tk.StringVar(value="Status: waiting")
        self.makao_state_var = tk.StringVar(value="Tura: - | Karta: -")
        self.makao_list_var = tk.StringVar(value="Brak graczy")

        self.log_text = None

        self.build_ui()
        self.start_server()
        self.refresh_dashboard()





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

    def make_title(self, parent, text, size=30):
        return tk.Label(
            parent,
            text=text,
            font=("Arial", size, "bold"),
            fg=self.text_color,
            bg=self.bg_color,
        )

    def make_panel(self, parent, bg=None, padx=18, pady=18):
        return tk.Frame(
            parent,
            bg=bg or self.panel_color,
            padx=padx,
            pady=pady,
            highlightthickness=1,
            highlightbackground=self.border_color,
        )

    def make_button(self, parent, text, command, bg=None, fg="#10231D", width=18):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 13, "bold"),
            bg=bg or self.gold,
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

    def make_label(self, parent, text=None, textvariable=None, bg=None, size=12, bold=False, wraplength=320):
        return tk.Label(
            parent,
            text=text,
            textvariable=textvariable,
            font=("Arial", size, "bold" if bold else "normal"),
            fg=self.text_color,
            bg=bg or self.panel_color,
            justify="left",
            anchor="w",
            wraplength=wraplength,
        )

    def build_ui(self):
        main = self.make_screen(padx=24, pady=18)

        top = tk.Frame(main, bg=self.bg_color)
        top.pack(fill="x", pady=(0, 12))

        self.make_title(top, "HOST GRY", size=34).pack(side="left")

        status_box = self.make_panel(top, bg=self.panel_color, padx=16, pady=10)
        status_box.pack(side="right")
        self.make_label(status_box, textvariable=self.server_status_var, bg=self.panel_color, size=12, bold=True).pack(anchor="w")
        self.make_label(status_box, textvariable=self.address_var, bg=self.panel_color, size=11).pack(anchor="w", pady=(3, 0))

        subtitle = tk.Label(
            main,
            text="Panel do uruchamiania Pokera i Makao bez wpisywania komend w konsoli",
            font=("Arial", 14),
            fg=self.muted_color,
            bg=self.bg_color,
        )
        subtitle.pack(anchor="w", pady=(0, 16))

        content = tk.Frame(main, bg=self.bg_color)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.columnconfigure(2, weight=1)
        content.rowconfigure(0, weight=1)

        poker_panel = self.build_game_panel(
            content,
            title="POKER TEXAS HOLD'EM",
            players_var=self.poker_players_var,
            bots_var=self.poker_bots_var,
            phase_var=self.poker_phase_var,
            state_var=self.poker_state_var,
            list_var=self.poker_list_var,
            start_command=lambda: self.start_game("POKER"),
            bot_command=lambda: self.add_bot("POKER"),
            accent=self.gold,
        )
        poker_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        makao_panel = self.build_game_panel(
            content,
            title="MAKAO",
            players_var=self.makao_players_var,
            bots_var=self.makao_bots_var,
            phase_var=self.makao_phase_var,
            state_var=self.makao_state_var,
            list_var=self.makao_list_var,
            start_command=lambda: self.start_game("MAKAO"),
            bot_command=lambda: self.add_bot("MAKAO"),
            accent=self.green,
        )
        makao_panel.grid(row=0, column=1, sticky="nsew", padx=8)

        log_panel = self.make_panel(content, bg=self.panel_color, padx=16, pady=16)
        log_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        tk.Label(
            log_panel,
            text="LOG HOSTA",
            font=("Arial", 16, "bold"),
            fg=self.text_color,
            bg=self.panel_color,
        ).pack(anchor="w")

        self.log_text = tk.Text(
            log_panel,
            width=34,
            height=20,
            bg=self.dark_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("Consolas", 10),
            relief="flat",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, pady=(12, 10))
        self.log_text.configure(state="disabled")

        bottom_buttons = tk.Frame(log_panel, bg=self.panel_color)
        bottom_buttons.pack(fill="x")
        self.make_button(bottom_buttons, "ODŚWIEŻ", self.refresh_dashboard, bg="#F8F7F2", width=10).pack(side="left")
        self.make_button(bottom_buttons, "WYCZYŚĆ LOG", self.clear_log, bg=self.blue, fg="white", width=12).pack(side="right")

    def build_game_panel(self, parent, title, players_var, bots_var, phase_var, state_var, list_var, start_command, bot_command, accent):
        panel = self.make_panel(parent, bg=self.table_color, padx=18, pady=18)

        tk.Label(
            panel,
            text=title,
            font=("Arial", 20, "bold"),
            fg=self.text_color,
            bg=self.table_color,
        ).pack(anchor="w", pady=(0, 12))

        stats = tk.Frame(panel, bg=self.table_color)
        stats.pack(fill="x", pady=(0, 12))
        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)

        self.make_stat_box(stats, players_var).grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.make_stat_box(stats, bots_var).grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        info_panel = self.make_panel(panel, bg=self.panel_color, padx=14, pady=12)
        info_panel.pack(fill="x", pady=(0, 12))
        self.make_label(info_panel, textvariable=phase_var, bg=self.panel_color, size=12, bold=True).pack(anchor="w")
        self.make_label(info_panel, textvariable=state_var, bg=self.panel_color, size=12).pack(anchor="w", pady=(5, 0))

        players_panel = self.make_panel(panel, bg=self.panel_color, padx=14, pady=12)
        players_panel.pack(fill="both", expand=True, pady=(0, 14))
        tk.Label(
            players_panel,
            text="LISTA GRACZY",
            font=("Arial", 13, "bold"),
            fg=self.text_color,
            bg=self.panel_color,
        ).pack(anchor="w")
        self.make_label(players_panel, textvariable=list_var, bg=self.panel_color, size=11, wraplength=260).pack(anchor="w", pady=(8, 0))

        self.make_button(panel, "DODAJ BOTA", bot_command, bg="#F8F7F2", width=18).pack(fill="x", pady=5)
        self.make_button(panel, "START GRY", start_command, bg=accent, width=18).pack(fill="x", pady=5)

        return panel

    def make_stat_box(self, parent, textvariable):
        box = self.make_panel(parent, bg=self.panel_color, padx=10, pady=10)
        tk.Label(
            box,
            textvariable=textvariable,
            font=("Arial", 12, "bold"),
            fg=self.text_color,
            bg=self.panel_color,
            justify="center",
        ).pack()
        return box





    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((BIND_HOST, PORT))
            self.server_socket.listen()
            self.server_socket.settimeout(0.5)
        except OSError as error:
            self.server_status_var.set("Błąd uruchomienia serwera")
            self.log(f"[BŁĄD] Nie udało się uruchomić serwera: {error}")
            messagebox.showerror("Błąd serwera", f"Nie udało się uruchomić serwera:\n{error}")
            return

        self.server_status_var.set("Serwer działa")
        self.log(f"[HOST] Serwer działa na porcie {PORT}. Klient z tego komputera: 127.0.0.1:{PORT}, z sieci LAN: {DEFAULT_SERVER}:{PORT}")

        self.accept_thread = threading.Thread(target=self.accept_loop, daemon=True)
        self.accept_thread.start()

    def accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self.safe_log(f"[CONNECT] Nowe połączenie: {addr}")
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
            thread.start()

    def handle_client(self, conn, addr):
        current_game = None
        player_id = None

        while self.running:
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

                msg = json.loads(msg_data.decode(FORMAT))
                game = msg.get("game")
                msg_type = msg.get("type")

                if game == "SYSTEM" and msg_type == "JOIN":
                    target = msg.get("data", {}).get("target_game")

                    if target in self.games:
                        current_game = self.games[target]
                        player_id = current_game.add_player(conn, addr)

                        send_json(conn, create_msg(
                            game="SYSTEM",
                            msg_type="JOINED",
                            player_id=player_id,
                            data={"game": target},
                        ))

                        self.safe_log(f"[{target}] Gracz {player_id} dołączył z {addr}")
                        self.safe_refresh()
                    else:
                        send_json(conn, create_msg(
                            game="SYSTEM",
                            msg_type="ERROR",
                            data={"message": "Nieznana gra"},
                        ))
                    continue

                if current_game:
                    current_game.handle_message(msg)
                    self.safe_refresh()

            except Exception as error:
                self.safe_log(f"[DISCONNECT] {addr}: {error}")
                break

        if current_game and player_id is not None:
            current_game.remove_player(player_id)
            self.safe_log(f"[{current_game.name}] Gracz {player_id} opuścił grę")
            self.safe_refresh()

        try:
            conn.close()
        except OSError:
            pass





    def start_game(self, game_name):
        game = self.games[game_name]
        total_players = len(game.players)

        if total_players < 2:
            messagebox.showwarning(
                "Za mało graczy",
                f"Do startu gry {game_name} potrzeba minimum 2 graczy lub botów."
            )
            return

        if self.is_game_started(game):
            messagebox.showinfo("Gra już trwa", f"Gra {game_name} jest już rozpoczęta.")
            return



        def run_start():
            try:
                game.start_game()
                self.safe_log(f"[{game_name}] START GRY")
            except Exception as error:
                self.safe_log(f"[{game_name}] BŁĄD STARTU GRY: {error}")
                self.root.after(0, messagebox.showerror, "Błąd startu gry", f"Nie udało się uruchomić gry {game_name}:\n{error}")
            finally:
                self.safe_refresh()

        threading.Thread(target=run_start, daemon=True).start()

    def add_bot(self, game_name):
        game = self.games[game_name]

        if self.is_game_started(game):
            messagebox.showwarning(
                "Gra już trwa",
                "Bota najlepiej dodać przed startem rundy. W tej wersji nie dodajemy botów w trakcie gry."
            )
            return

        player_id = game.add_bot()
        if game_name == "POKER":
            self.log(f"[{game_name}] Dodano bota Monte Carlo jako Gracz {player_id}")
        else:
            self.log(f"[{game_name}] Dodano bota jako Gracz {player_id}")
        self.refresh_dashboard()





    def is_game_started(self, game):
        return bool(getattr(game, "game_state", {}).get("game_started", False))

    def get_players_info(self, game):
        humans = []
        bots = []

        for player in list(game.players):
            player_id = player[0]
            conn = player[1] if len(player) > 1 else None
            is_bot = False

            if len(player) >= 4:
                is_bot = bool(player[3])
            elif conn is None:
                is_bot = True

            if is_bot:
                bots.append(player_id)
            else:
                humans.append(player_id)

        return humans, bots

    def format_players(self, humans, bots):
        lines = []
        for player_id in humans:
            lines.append(f"Gracz {player_id} — człowiek")
        for player_id in bots:
            lines.append(f"Gracz {player_id} — bot")
        return "\n".join(lines) if lines else "Brak graczy"

    def refresh_dashboard(self):
        poker = self.games["POKER"]
        p_humans, p_bots = self.get_players_info(poker)
        p_state = poker.game_state
        p_turn = p_state.get("current_turn")
        p_turn_text = "-"
        if p_turn is not None and 0 <= p_turn < len(poker.players):
            p_turn_text = str(poker.players[p_turn][0])

        self.poker_players_var.set(f"Gracze: {len(p_humans) + len(p_bots)}")
        self.poker_bots_var.set(f"Boty: {len(p_bots)}")
        self.poker_phase_var.set(f"Faza: {p_state.get('phase', 'waiting')} | Tura: {p_turn_text}")
        self.poker_state_var.set(f"Pula: {p_state.get('pot', 0)} | Bet: {p_state.get('current_bet', 0)}")
        self.poker_list_var.set(self.format_players(p_humans, p_bots))

        makao = self.games["MAKAO"]
        m_humans, m_bots = self.get_players_info(makao)
        m_state = makao.game_state
        table = m_state.get("table")
        table_card = "-"
        if table:
            try:
                table_card = str(table[-1])
            except Exception:
                table_card = str(table)

        m_status = "started" if m_state.get("game_started") else "waiting"
        self.makao_players_var.set(f"Gracze: {len(m_humans) + len(m_bots)}")
        self.makao_bots_var.set(f"Boty: {len(m_bots)}")
        self.makao_phase_var.set(f"Status: {m_status}")
        self.makao_state_var.set(f"Tura: {m_state.get('current_turn', '-')} | Karta: {table_card}")
        self.makao_list_var.set(self.format_players(m_humans, m_bots))

        if self.running:
            self.root.after(700, self.refresh_dashboard)

    def safe_refresh(self):
        if self.running:
            self.root.after(0, self.refresh_dashboard)





    def log(self, text):
        print(text)
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def safe_log(self, text):
        if self.running:
            self.root.after(0, self.log, text)

    def clear_log(self):
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")





    def close_app(self):
        self.running = False

        try:
            if self.server_socket is not None:
                self.server_socket.close()
        except OSError:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HostGuiApp(root)
    root.mainloop()
