
import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from poker import PokerGame

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

CASES = ROOT / "tests" / "blackbox" / "cases"


def normalize_keys(value):
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items()}
    return value


def load_state(path: Path):
    with path.open("r", encoding="utf-8") as file:
        state = json.load(file)
    state["folded_players"] = set(state.get("folded_players", []))
    state["players_acted"] = set(state.get("players_acted", []))
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
    for key, value in defaults.items():
        state.setdefault(key, value)
    return state


def run_case(input_file: Path, output_file: Path):
    state_in = load_state(input_file)
    state_out = load_state(output_file)

    game = PokerGame(send_json=lambda conn, msg: None, create_msg=lambda *args, **kwargs: {})
    game.game_state = state_in

    for player_id in state_in["hands"].keys():
        game.players.append((str(player_id), None, None))

    start_phase = game.game_state["phase"]

    with contextlib.redirect_stdout(io.StringIO()):
        if start_phase != "showdown":
            safety_counter = 0
            while game.game_state["phase"] == start_phase and game.game_state["game_started"]:
                safety_counter += 1
                if safety_counter > 1000:
                    raise RuntimeError("Przekroczono limit ruchów w teście")

                current_turn_idx = game.game_state["current_turn"]
                if current_turn_idx is None or current_turn_idx >= len(game.players):
                    break

                current_player_id = game.players[current_turn_idx][0]
                game.handle_message({
                    "type": "MOVE",
                    "player_id": current_player_id,
                    "data": {"action": "CALL"},
                })

        if game.game_state["phase"] == "showdown" and start_phase != "river":
            game.showdown_locked()

    actual_chips = normalize_keys(game.game_state["chips"])
    expected_chips = normalize_keys(state_out["chips"])

    return (
        game.game_state["phase"] == state_out["phase"]
        and actual_chips == expected_chips
        and int(game.game_state["pot"]) == int(state_out["pot"])
    )


def main():
    ok = 0
    failed = 0
    missing = 0

    for input_file in sorted(CASES.glob("*.in")):
        output_file = input_file.with_suffix(".out")
        if not output_file.exists():
            print(f"{input_file.name} {RED}brak pliku .out{RESET}")
            missing += 1
            continue
        try:
            success = run_case(input_file, output_file)
        except Exception as error:
            print(f"{input_file.name} {RED}error: {error}{RESET}")
            failed += 1
            continue

        if success:
            print(f"{input_file.name} {GREEN}succes{RESET}")
            ok += 1
        else:
            print(f"{input_file.name} {RED}failed{RESET}")
            failed += 1

    print("-" * 60)
    print(f"Wynik: OK={ok}, błędne={failed}, brakujące={missing}")
    return 0 if failed == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
