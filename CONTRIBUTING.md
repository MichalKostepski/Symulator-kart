# Contributing to Poker & Makao Hub

This is an educational **three-person university project** retained as a technical portfolio. Contributions and bug reports are welcome, but changes should preserve existing gameplay semantics and acknowledge the original team.

## Development setup

- Install Python 3.11+ with Tkinter; the app has no external runtime dependencies.
- Start the host with `python app/host_gui.py` and the client with `python app/client.py` from the repository root.
- Use a **trusted LAN only**; the network protocol is not authenticated or encrypted.

## Before proposing a change

1. Run `python scripts/run_all_tests.py`.
2. For UI-related changes, run `python scripts/gui_smoke.py` on a graphical desktop, then walk through `docs/MANUAL_QA.md`.
3. Add or extend a regression test for a rule, parser, protocol, or data-model bug.
4. Do not commit `__pycache__`, coverage reports, user statistics, personal information, or screenshots showing real participants.
5. Keep test fixtures deterministic; do not replace genuine GUI captures with mockups.
6. Explain any change to protocol framing or game rules in the pull request.

Automated CI covers Python 3.11/3.12 on Windows and Ubuntu, plus a Linux Tkinter startup smoke test. It does not certify full multiplayer gameplay or public-network security.

## Repository ownership and assets

Original authors: **Rafał Koper, Piotr Horodecki, Michał Kostępski**. Source code, university documents and bundled card graphics have no asserted blanket open-source license. Ask the contributors before reusing material beyond browsing the repository. See `docs/SECURITY.md`.
