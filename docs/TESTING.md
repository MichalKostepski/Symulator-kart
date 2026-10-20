# Testing strategy

Run from the **repository root** with Python 3.11+.

## Repeatable suite

```bash
python scripts/run_all_tests.py
```

The script stops with a non-zero exit status if any stage fails:

1. `scripts/run_unit_tests.py` — the existing poker and Makao unit tests plus additional portfolio regression tests for cards, decks, framed JSON and local statistics.
2. `scripts/run_whitebox_tests.py` — internal state transitions, effects, bets and persistence.
3. `scripts/run_blackbox_poker.py` — all `*.in`/`*.out` fixtures in `tests/blackbox/cases`, checking phase, stacks and pot after the scripted action(s).

A missing expected `.out` file or an unexpected exception is a failure. The black-box suite also fails if there are no input cases, preventing accidental "zero tests passed" success.

**Original university test corpus:** 23 unit tests, 9 white-box tests and 78 black-box poker pairs. The portfolio suite adds small, independently maintainable regression tests. The actual CI run, rather than a static README assertion, is the source of truth for pass/fail.

## Continuous integration

`.github/workflows/python-tests.yml` runs on `MAIN_NEW` pushes, pull requests and manual dispatch.

Matrix: **Ubuntu / Windows × Python 3.11 / 3.12**.

Stages:
- Compile Python modules to catch syntax errors.
- Run the complete non-GUI suite in a clean runner, without third-party dependencies.

The workflow deliberately avoids fabricating GUI coverage on machines without an interactive desktop.

## GUI and LAN testing

The existing `tests/unit/client_test.py` and `tests/unit/host_test.py` create Tk windows and rely on GUI behavior; they are excluded from headless CI by design. Run them only in a configured graphical session:

```bash
python -m unittest tests/unit/client_test.py tests/unit/host_test.py
```

Results may depend on display environment and should be reported separately. Use [Manual QA](MANUAL_QA.md) for testing actual host/client interaction, AI turns, disconnections, firewall prompts and different desktop resolutions.

## Out of scope

This automated suite does **not** prove correct visual layout, Windows `.vbs` behavior, external LAN connectivity, arbitrary hostile network traffic, accessibility or internet readiness. The game contains no real-money wagers.
