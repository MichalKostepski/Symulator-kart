# Poker & Makao Hub

**A LAN multiplayer card-game desktop application built in Python.** Two games, a host/client architecture, Tkinter interfaces, playable bots and automated game-logic tests — created as a three-person university software-engineering project.

[![Python tests](https://github.com/MichalKostepski/Symulator-kart/actions/workflows/python-tests.yml/badge.svg?branch=MAIN_NEW)](https://github.com/MichalKostepski/Symulator-kart/actions/workflows/python-tests.yml)

**Python 3.11+ · Tkinter · TCP sockets · JSON · threading · unittest · standard library only**

> **Project status:** University prototype / portfolio project, not a public internet gaming service. It is designed for trusted local networks and uses virtual poker chips only. This repository contains collaborative work by **Rafał Koper, Piotr Horodecki and Michał Kostępski**; see [Credits](#credits).

## Why we built it

We wanted to bring the basic card-table experience to computers on the same network, without requiring users to set up a dedicated game server or install third-party Python packages. The interesting challenge was keeping several components in sync: the host's authoritative game state, each player's interface, turn rules, bot decisions and messages sent over TCP.

## Features at a glance

| | Texas Hold'em Poker | Makao |
| --- | --- | --- |
| Gameplay | Community cards, blinds, betting rounds, fold / call / raise, showdown | Turn-based play, drawing, card effects, suit/rank requests, Makao calls |
| Bots | Monte Carlo hand-equity estimation with pot-odds heuristics | Rule-based card scoring and action selection |
| Multiplayer | Host + clients over LAN | Host + clients over LAN |
| Interface | Poker table, hand and controls | Card hand, active card and turn controls |
| Testing | Unit, white-box and **78 data-driven black-box scenarios** | Unit and white-box tests |

**Shared features:** host dashboard, chat, customizable client appearance, rules screens and local win/loss history. The interface was primarily designed around a 1920 × 1080 desktop, with scrollbars on smaller displays.

## Get started — Windows

**Requirements:** Python 3.11 or newer with Tkinter and an available TCP port **5050**. No `pip install` or API keys are needed.

### Play on one computer

1. Download or clone the repository.
2. Open the `uruchomienie` folder.
3. Double-click **`03_URUCHOM_HOSTA_I_KLIENTA.vbs`**. The script opens the host and client applications.
4. In the client, choose **POKER** or **MAKAO** and connect to `127.0.0.1` if the server is on the same PC.
5. Use the host dashboard to add bots or wait for other players, then start the game.

If you prefer visible console output (recommended for the first run), open **two PowerShell windows** in the repository root:

```powershell
# Window 1 — start the host
py -3 app/host_gui.py
```

```powershell
# Window 2 — start a player client
py -3 app/client.py
```

Run the host first. Windows Firewall may ask for permission to receive local-network connections; allow it only on a **private, trusted network**.

### Play across the LAN

Launch the host on one computer and clients on other computers **on the same trusted local network**. In the client, enter the host computer's LAN IPv4 address (shown in the host window), and use port **5050**. A router or firewall can prevent connections; do **not** expose this server through public port forwarding.

**Linux / macOS:** Try `python3 app/host_gui.py` and `python3 app/client.py` in separate terminals. Tkinter must be installed (on Debian/Ubuntu, typically `python3-tk`). Automated logic tests run on Linux, but complete GUI/gameplay verification is still a manual step. Windows `.vbs` launchers do not work on Linux/macOS.

## Architecture

```text
                     Trusted local network (TCP :5050)
  +----------------------+             +----------------------+
  | Host GUI             |             | Player client(s)     |
  | app/host_gui.py      |<-- JSON --->| app/client.py        |
  +----------+-----------+             +-----------+----------+
             |                                      |
     +-------+--------+                   +---------+---------+
     |                |                   | Local statistics  |
  +--v---------+  +---v--------+          | app/stats_manager |
  | PokerGame  |  | MakaoGame  |          +-------------------+
  | poker.py   |  | makao.py   |
  +--+---------+  +---+--------+
     |                |
  +--v---------+  +---v--------+
  | PokerBot   |  | Makao bot  |
  | Monte Carlo|  | Heuristics |
  +------------+  +------------+
```

The server owns the game rules and state; clients send actions and render updates. Network messages are JSON with a fixed-size **64-byte ASCII length header**, followed by UTF-8 payload bytes. Game-state operations use locks to coordinate connection-handler threads.

See [Architecture & protocol](docs/ARCHITECTURE.md) and the original [UML component diagram](docs/04_diagramy_i_harmonogram/Diagram_Komponentow.png). The `docs/` tree also preserves the university project's requirements, design, test documentation, diagrams and schedule.

## Run the tests

The project uses Python's built-in `unittest` framework and a data-driven black-box runner; no dependencies need installing.

```powershell
python scripts/run_all_tests.py
```

Or run each layer separately:

```powershell
python scripts/run_unit_tests.py
python scripts/run_whitebox_tests.py
python scripts/run_blackbox_poker.py
```

The existing suite includes **23 original unit tests**, **9 white-box tests** and **78 black-box poker fixtures**, with additional core-model/protocol regression tests in this portfolio version. Actual results are reported by the [GitHub Actions workflow](https://github.com/MichalKostepski/Symulator-kart/actions/workflows/python-tests.yml) for Python 3.11/3.12 on Ubuntu and Windows.

GUI-focused tests in `tests/unit/client_test.py` and `tests/unit/host_test.py` are **not part of the default headless suite**; they require a working Tk desktop and may need environment-specific setup. For a reproducible human check, use [Manual QA checklist](docs/MANUAL_QA.md).

See [Testing strategy](docs/TESTING.md) for coverage scope and limitations.

## Repository guide

| Location | Responsibility |
| --- | --- |
| `app/host_gui.py` | Server lifecycle, host dashboard, client connections and dispatch |
| `app/client.py` | Tkinter player UI, card drawing, networking and local stats |
| `app/poker.py`, `app/makao.py` | Game rules and round transitions |
| `app/poker_bot.py`, `app/makao.py` | Poker equity estimation and Makao bot decisions |
| `app/card*.py`, `app/deck*.py` | Deck/card data structures |
| `app/stats_manager.py` | Plain-text local statistics and match history |
| `tests/` | Unit, white-box, black-box and optional GUI tests |
| `scripts/` | Repeatable test commands |
| `docs/` | Requirements, UML, project documentation and technical notes |
| `uruchomienie/` | Windows double-click launchers |

**Local player data:** `data/stats.txt` and `data/history.txt` are created and updated on your machine. They are deliberately **not tracked** in the portfolio repository; your playing history stays local.

## Engineering choices and trade-offs

- **Standard library only:** simpler installation; Tkinter is provided with most Python distributions.
- **Host-authoritative game state:** client actions are processed by the game logic rather than trusting a rendered card-table state.
- **Monte Carlo bot:** samples unknown cards and estimates equity rather than relying exclusively on fixed hand rankings.
- **Automated rules testing:** input/output poker fixtures exercise winners, ties and pot distribution separately from the UI.
- **Boundaries:** no user authentication, encryption, anti-cheat hardening, matchmaking, internet hosting or commercial gambling features. This is an educational LAN prototype, not a hardened network service.

Detailed technical limitations and disclosure guidance are in [Security & limitations](docs/SECURITY.md).

## Credits

Developed as a **group university project** by **Rafał Koper, Piotr Horodecki and Michał Kostępski**. The university documentation identifies all three contributors; this portfolio repository does not claim that any individual wrote the entire application.

The repository includes course deliverables and card graphics. Their original authorship/licensing has not been independently verified, so **no open-source license is asserted for the complete repository**. Contact the contributors before copying or redistributing assets/code outside the scope of viewing this public portfolio.

## More

- [Architecture & network protocol](docs/ARCHITECTURE.md)
- [Testing guide](docs/TESTING.md)
- [Manual desktop QA checklist](docs/MANUAL_QA.md)
- [Security & limitations](docs/SECURITY.md)
- [Portfolio project summary](docs/PORTFOLIO.md)
