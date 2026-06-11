# Notatki do prezentacji projektu

Proponowany układ prezentacji demo projektu **Poker / Makao Hub**.

## Slajd 1 — Tytuł
**Poker / Makao Hub**  
Aplikacja do gry w Pokera i Makao w sieci LAN oraz z botami.

## Slajd 2 — Problem
Nie zawsze mamy fizyczne karty, żetony i komplet graczy. Projekt rozwiązuje ten problem przez aplikację, która pozwala uruchomić grę lokalnie na komputerach w jednej sieci.

## Slajd 3 — Cel projektu
Celem było stworzenie prostego huba z dwiema grami karcianymi, GUI, botami, chatem, statystykami i historią rozgrywek.

## Slajd 4 — Wymagania funkcjonalne
- wybór Pokera lub Makao,
- gra w LAN,
- dodawanie botów,
- chat,
- zasady gry,
- statystyki i historia,
- zmiana wyglądu interfejsu.

## Slajd 5 — Wymagania niefunkcjonalne
- prosty i czytelny interfejs,
- stabilna komunikacja host-klient,
- lokalny zapis danych,
- brak hazardu,
- działanie w Pythonie z wykorzystaniem standardowych bibliotek.

## Slajd 6 — Architektura
Pokazać folder `app/` i omówić:
- `host_gui.py` — serwer i panel hosta,
- `client.py` — GUI gracza,
- `poker.py` i `makao.py` — logika gier,
- `poker_bot.py` i `makao_bot.py` — boty,
- `stats_manager.py` — statystyki.

## Slajd 7 — Poker
Pokazać najważniejsze mechanizmy: żetony, blindy, fold/call/raise, fazy gry, showdown i ocenę układów.

## Slajd 8 — Makao
Pokazać mechanikę kart funkcyjnych, dobierania kart, blokowania tury, żądania koloru/figury i mechanizm Makao.

## Slajd 9 — Testy
Powiedzieć, że projekt zawiera:
- 23 testy jednostkowe,
- 78 testów czarnoskrzynkowych Pokera,
- raporty coverage.

Wynik testów:
```text
Ran 23 tests — OK
Wynik blackbox: OK=78, błędne=0, brakujące=0
```

## Slajd 10 — Demo
Kroki demo:
1. Otworzyć folder `uruchomienie/`.
2. Kliknąć `03_URUCHOM_HOSTA_I_KLIENTA.vbs`, który uruchamia aplikację bez dodatkowego okna `cmd`.
3. Połączyć klienta z hostem.
4. Wybrać grę.
5. Dodać bota.
6. Rozpocząć rozgrywkę.
7. Pokazać chat, ruch gracza i aktualizację stołu.
8. Wspomnieć, że interfejs został dopasowany do formatu 1920 × 1080 i ma przewijanie na mniejszych ekranach.

Można też uruchomić osobno `01_URUCHOM_HOSTA.vbs`, a potem `02_URUCHOM_KLIENTA.vbs`.

## Slajd 11 — Co się udało
- działają dwie gry,
- jest komunikacja LAN,
- jest GUI,
- są boty,
- są statystyki i historia,
- są testy i dokumentacja.

## Slajd 12 — Możliwy rozwój
- gra przez Internet,
- konta użytkowników,
- ranking,
- zapis w bazie danych,
- ulepszenie botów,
- instalator.
