# Portfolio summary — Poker & Makao Hub

**Type:** Three-person university software-engineering group project.

**Technologies:** Python, Tkinter, TCP sockets, threading, JSON, unittest.

**Problem:** Make classic card games playable from multiple desktops over a trusted local network while preserving shared, authoritative game state.

**Delivered functionality:** Poker Texas Hold'em and Makao, host/client interfaces, turn-based rules and card effects, chat, bots (including Monte Carlo equity estimation for Poker), player-local results and testing resources.

**Engineering topics illustrated:**
- Message framing over a TCP byte stream; client/server event handling.
- Synchronization of multiplayer turns and shared state.
- Hand evaluation, tie-breaking and pot distribution in Poker.
- Rule-based bot selection and Monte Carlo simulation.
- Black-box, unit and white-box tests for domain logic.
- Tkinter application lifecycle and Windows desktop tooling.

**Collaboration:** The university documentation credits Rafał Koper, Piotr Horodecki and Michał Kostępski. Avoid suggesting any single author implemented every subsystem; individual contributions should be described only when supported by the author's own account.

**Honest limitations:** LAN only, plain-text statistics, no security hardening or production deployment, and GUI scenarios require manual testing.

**CV-ready concise description:**

> **Poker & Makao Hub — Python/Tkinter LAN multiplayer game (team project).** Developed a desktop card-game application with TCP/JSON client–server communication, game-state management, bots and automated logic tests. The codebase includes Poker equity simulation, Makao card effects, UML documentation and repeatable test workflows.

This describes the joint result, not a verified breakdown of individual work. Tailor it to concrete personal contributions during an interview.
