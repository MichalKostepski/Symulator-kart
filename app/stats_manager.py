import os
from datetime import datetime

class StatsManager:
	def __init__(self, stats_file=None, history_file=None):


		base_dir = os.path.dirname(os.path.abspath(__file__))
		project_dir = os.path.dirname(base_dir)
		data_dir = os.path.join(project_dir, "data")
		os.makedirs(data_dir, exist_ok=True)

		self.stats_file = stats_file or os.path.join(data_dir, "stats.txt")
		self.history_file = history_file or os.path.join(data_dir, "history.txt")

		self.stats = {
		 "CHIPS_RESULT": 0,
		 "GAMES_PLAYED": 0,
		 "MAKAO_LOSES": 0,
		 "MAKAO_WINS": 0,
		 "POKER_HANDS_WON": 0,
		 "POKER_GAMES": 0,
		 "MAKAO_GAMES": 0
		}
		self.load_stats()

	def load_stats(self):
		if os.path.exists(self.stats_file):
			try:
				with open(self.stats_file, 'r') as f:
					f_text = f.readlines()
					for line in f_text:
						if ':' in line:
							key, val = line.split(':')
							key = key.strip()
							if key in self.stats:
								self.stats[key] = int(val.strip())
			except Exception as e:
				print(f"Błąd podczas wczytywania statystyk: {e}")

	def load_history(self):
		if os.path.exists(self.history_file):
			try:
				with open(self.history_file, 'r') as f:
					f_text = f.readlines()
					return f_text
			except Exception as e:
				print(f"Błąd podczas odczytywania historii: {e}")
		else:
			return []

	def save_stats(self):
		try:
			with open(self.stats_file, 'w') as f:
				new_stats = (
				 f"CHIPS_RESULT: {self.stats['CHIPS_RESULT']}\n"
				 f"GAMES_PLAYED: {self.stats['GAMES_PLAYED']}\n"
				 f"MAKAO_LOSES: {self.stats['MAKAO_LOSES']}\n"
				 f"MAKAO_WINS: {self.stats['MAKAO_WINS']}\n"
				 f"POKER_HANDS_WON: {self.stats['POKER_HANDS_WON']}\n"
				 f"POKER_GAMES: {self.stats['POKER_GAMES']}\n"
				 f"MAKAO_GAMES: {self.stats['MAKAO_GAMES']}"
				)
				f.write(new_stats)
		except Exception as e:
			print(f"Błąd podczas zapisu statystyk: {e}")

	def log_game(self, game_played, result):
		date_game = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		line = f"{game_played} {result} {date_game}\n"
		try:
			with open(self.history_file, 'a') as f:
				f.write(line)
		except Exception as e:
			print(f"Błąd podczas zapisu historii: {e}")


	def update_after_game(self, game_type, chips_delta, won):
		self.stats["GAMES_PLAYED"] += 1
		self.stats["CHIPS_RESULT"] += chips_delta

		if game_type.lower() == "poker":
			self.stats["POKER_GAMES"] += 1
			if won:
				self.stats["POKER_HANDS_WON"] += 1
				self.log_game("Poker", "Win")
			else:
				self.log_game("Poker", "Loss")

		elif game_type.lower() == "makao":
			self.stats["MAKAO_GAMES"] += 1
			if won:
				self.stats["MAKAO_WINS"] += 1
				self.log_game("Makao", "Win")
			else:
				self.stats["MAKAO_LOSES"] += 1
				self.log_game("Makao", "Loss")

		self.save_stats()

	def format_stats(self):
	    return (
	        f"Rozegrane gry: {self.stats['GAMES_PLAYED']}\n"
	        f"Makao: {self.stats['MAKAO_GAMES']}  |  Wygrane: {self.stats['MAKAO_WINS']}  |  Przegrane: {self.stats['MAKAO_LOSES']}\n"
	        f"Poker: {self.stats['POKER_GAMES']}  |  Wygrane ręce: {self.stats['POKER_HANDS_WON']}\n"
	        f"Wynik żetonów: {self.stats['CHIPS_RESULT']}"
	    )