from poker import PokerGame
import json
import sys
import os
from io import StringIO

old_stdout = sys.stdout
sys.stdout = StringIO()

def normalize_keys(d):
	if not isinstance(d, dict):
		return d
	return {str(k): v for k, v in d.items()}

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def main():
	if len(sys.argv) < 3:
		print("Brak plikow wejsciowych")
		return

	file_name1 = sys.argv[1]
	file_name2 = sys.argv[2]

	if not os.path.exists(file_name1) or not os.path.exists(file_name2):
		print(f"Plik nie istnieje")
		return

	try:
		with open(file_name1, 'r', encoding='utf-8') as f:
			state_in = json.load(f)

		state_in["folded_players"] = set(state_in["folded_players"])
		state_in["players_acted"] = set(state_in["players_acted"])
		
	except Exception as e:
		print(f"Blad odczytu {file_name1} {e}")
		return

	try:
		with open(file_name2, 'r', encoding='utf-8') as f:
			state_out = json.load(f)

		state_out["folded_players"] = set(state_out["folded_players"])
		state_out["players_acted"] = set(state_out["players_acted"])

	except Exception as e:
		print(f"Blad odczytu {file_name2} {e}")
		return

	defaults = {
		"deck": None,
		"hands": {},
		"chips": {},
		"community_cards": [],
		"pot": 0,
		"current_bet": 0,
		"phase": "waiting",
		"blind_amount": 10,
		"blind_player": 0,
		"current_turn": None,
		"round_bets": {},
		"folded_players": set(),
		"players_acted": set(),
		"game_started": False,
	}
	for k, v in defaults.items():
		if k not in state_in:
			state_in[k] = v



	game = PokerGame(send_json=lambda conn, msg: None, create_msg=lambda *args, **kwargs: {})

	game.game_state = state_in

	for player_id in state_in["hands"].keys():
		game.players.append((str(player_id), None, None))

	start_phase = game.game_state["phase"]

	if start_phase != "showdown":
		while game.game_state["phase"] == start_phase and game.game_state["game_started"]:
			current_turn_idx = game.game_state["current_turn"]

			if current_turn_idx is None or current_turn_idx >= len(game.players):
				break

			current_player_id = game.players[current_turn_idx][0]

			game.handle_message({
				"type": "MOVE",
				"player_id": current_player_id,
				"data": {"action": "CALL"}
			})

	if game.game_state["phase"] == "showdown" and start_phase != "river":
		try:
			game.showdown_locked()
		finally:
			sys.stdout = old_stdout

		actual_chips = normalize_keys(game.game_state["chips"])
		expected_chips = normalize_keys(state_out["chips"])


		if game.game_state["phase"] == state_out["phase"] and actual_chips == expected_chips and int(game.game_state["pot"]) == int(state_out["pot"]):
			print(f"{file_name1} {GREEN}succes{RESET}")
		else:
			print(f"{file_name1} {RED}failed{RESET}")



if __name__ == "__main__":
	main()