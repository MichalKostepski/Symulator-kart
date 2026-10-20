# Architecture and network protocol

This page describes the actual implementation on branch `MAIN_NEW`, not a proposed redesign.

## Processes and responsibilities

**Host** — `app/host_gui.py` creates a Tkinter control panel, binds a TCP listening socket on `0.0.0.0:5050` and manages connected clients. It owns an instance of `PokerGame` and `MakaoGame`, and dispatches incoming JSON actions to the chosen game.

**Client** — `app/client.py` is a Tkinter application that connects to the host, displays game state, sends user actions and keeps local match statistics through `StatsManager`.

**Game logic** — `app/poker.py` and `app/makao.py` implement rules and state transitions. Shared behavior is defined by the abstract `Game` class in `app/game.py`. Deck/card models live in `app/card.py`, `app/deck.py` and the simplified model variants.

**Bots** — the poker bot (`app/poker_bot.py`) estimates equity with randomly generated opponent hands and remaining community cards. The Makao bot's move-selection logic is implemented in `MakaoGame.run_bot`, using card weights; `app/makao_bot.py` holds the bot's game/player references.

## Message framing

TCP is a stream: a single `recv` does not necessarily return one complete message. Both host and client implement `recv_exact` to read a precise number of bytes.

A message is encoded as:

1. **64 bytes of ASCII**: decimal UTF-8 payload length, right-padded with spaces.
2. **N bytes of UTF-8**: JSON payload.

A typical logical message envelope looks like:

```json
{
  "game": "POKER",
  "type": "MOVE",
  "player_id": 1,
  "data": {"action": "CALL"},
  "chat": null
}
```

The `game` field identifies the game context; the `type` field identifies the action or response. Actual message types depend on the game (for example, `JOIN`, `MOVE`, `TURN`, `TABLE`, `PLAY`, `DRAW` and `CHAT`).

## Execution and synchronization

- The host accepts client connections over TCP and processes game actions in connection-handler threads.
- Game objects maintain their own player lists and state dictionaries.
- The `Game` base class provides a re-entrant lock (`threading.RLock`), used in game logic to coordinate modifications.
- Player clients are responsible for displaying received state and sending requested actions.
- The host's UI is a separate Tkinter event loop; network and UI lifecycle should be tested together on a real desktop.

## Persistence

`StatsManager` stores player-local counters and game results in `data/stats.txt` and `data/history.txt`. These files contain runtime data, not portable game fixtures. They are ignored by Git and recreated as required on the user's machine.

## Deliberate limits

This is a trusted-LAN project: there is **no authentication, encrypted transport, message size cap, or internet exposure protection**. It should not be run on untrusted networks or opened to the public internet. Tkinter rendering and actual multi-machine behavior require manual testing beyond the automated game-logic suite.
