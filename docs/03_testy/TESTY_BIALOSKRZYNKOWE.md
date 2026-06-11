# Testy białoskrzynkowe

Testy białoskrzynkowe znajdują się w folderze:

```text
tests/whitebox/test_whitebox_logic.py
```

Ich celem jest sprawdzenie nie tylko wyniku widocznego dla użytkownika, ale konkretnych wewnętrznych gałęzi kodu i stanów aplikacji.

## Co sprawdzają testy?

### Poker

1. `parse_card()` — obsługa różnych formatów zapisu kart, np. `ace of spades`, `10H`, `Q♦`.
2. `is_straight()` — specjalny przypadek strita z asem jako niską kartą, czyli A-2-3-4-5.
3. `get_next_active_turn()` — pomijanie gracza, który spasował, oraz gracza bez żetonów.
4. `is_betting_round_over()` — przypadek, gdy pozostali gracze są all-in i nie ma już kto licytować.

### Makao

1. `add_effect()` — sumowanie kar za karty 2, 3 i króla pik/kier.
2. `add_effect()` — czyszczenie efektu po królu trefl/karo.
3. `check_card_eligibility()` — po dobraniu można zagrać tylko dobraną kartę pasującą do stołu.
4. `resolve_effect()` — blokada tury zwiększa licznik blokady aktualnego gracza.

### Statystyki

1. `StatsManager.update_after_game()` — aktualizacja liczników i zapis do plików `stats.txt` oraz `history.txt`.

## Uruchomienie

```bash
python scripts/run_whitebox_tests.py
```

Wynik w aktualnej wersji:

```text
Ran 9 tests
OK
```

## Dlaczego to są testy białoskrzynkowe?

Ponieważ zostały napisane na podstawie znajomości kodu źródłowego. Testy celowo wchodzą w konkretne metody pomocnicze i ustawiają wewnętrzny stan gry, np. `game_state`, `effect`, `blocked`, `folded_players`, `round_bets`. Dzięki temu sprawdzają konkretne ścieżki wykonania programu, a nie tylko zachowanie aplikacji z perspektywy użytkownika.
