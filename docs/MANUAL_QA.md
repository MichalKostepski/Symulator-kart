# Manual QA checklist (Windows / trusted LAN)

Record the date, Python version, OS and result for each check. Do not mark unperformed checks as passed.

## One-computer smoke test

- [ ] From the project root, run `py -3 app/host_gui.py` and confirm a host window opens and binds port 5050.
- [ ] In a second PowerShell window, run `py -3 app/client.py`; confirm the client UI appears.
- [ ] Enter `127.0.0.1` in the client and connect to the host.
- [ ] Select Poker. Confirm the host counts the client and can add a poker bot.
- [ ] Start a Poker game; check dealing, turn progression and `CALL`/`FOLD`/`RAISE` controls.
- [ ] Return to the menu, select Makao, add a Makao bot and start a game.
- [ ] Check playing a legal card, drawing, special-card effect and end-of-turn behavior.
- [ ] Test chat and confirm messages appear on the other connected client.
- [ ] Complete a match and confirm local stats/history are written under `data/`.
- [ ] Close both windows; start again and check that stats can be loaded.
- [ ] Relaunch using `uruchomienie/03_URUCHOM_HOSTA_I_KLIENTA.vbs` and verify both windows start.

## Multiple computers and edge cases

- [ ] On a second Windows computer in the **same private LAN**, connect using the host's LAN IPv4 address.
- [ ] Check Windows Firewall configuration without enabling public-network access.
- [ ] Disconnect a client during play; check host/client handling and game state.
- [ ] Attempt an invalid move and verify the game does not process it as a valid turn.
- [ ] Test a smaller screen than 1920×1080: scrollbars and important controls remain reachable.
- [ ] Verify card assets load correctly in both available client card styles.

## Results template

| Date / platform | Scenario | Pass / Fail / Not run | Notes |
| --- | --- | --- | --- |
| YYYY-MM-DD / Windows / Python 3.x | Poker on one PC | Not run | Fill in after manual verification |

**Important:** This list is a manual test plan, not a claim that all scenarios have been executed.
