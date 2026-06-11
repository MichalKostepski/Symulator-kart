# Poker / Makao Hub

Projekt zaliczeniowy z Inżynierii Oprogramowania: **hub z dwiema grami karcianymi — Poker Texas Hold'em oraz Makao**.
Aplikacja została napisana w języku **Python** i działa w modelu **host-klient w sieci LAN**. Projekt zawiera GUI, logikę obu gier, boty, chat, lokalne statystyki, historię rozgrywek, dokumentację oraz testy.

---

## 1. Cel projektu

Celem projektu było stworzenie prostej aplikacji rekreacyjnej, która pozwala zagrać w gry karciane bez fizycznych kart i żetonów.
System umożliwia:

- wybór gry: **Poker** albo **Makao**,
- grę wieloosobową w sieci lokalnej LAN,
- grę z botami,
- korzystanie z chatu,
- zmianę wyglądu interfejsu,
- podgląd zasad gry,
- zapis statystyk i historii rozgrywek.

Projekt **nie obsługuje hazardu** — w Pokerze używane są wyłącznie wirtualne żetony.

---

## 2. Technologie

Projekt korzysta z:

- **Python 3**,
- **Tkinter**,
- **socket**,
- **threading**,
- **json**,
- **unittest**,
- plików tekstowych `stats.txt` i `history.txt`.

Projekt nie wymaga instalowania dodatkowych bibliotek z `pip`.
Na Linuxie może być potrzebny pakiet systemowy `python3-tk`, ponieważ GUI korzysta z Tkintera.

---

## 3. Struktura folderów

```text
projekt_10_06/
├── app/
│   ├── host_gui.py
│   ├── client.py
│   ├── poker.py
│   ├── makao.py
│   ├── poker_bot.py
│   ├── makao_bot.py
│   ├── game.py
│   ├── card.py
│   ├── deck.py
│   ├── card_simple.py
│   ├── deck_simple.py
│   ├── stats_manager.py
│   └── assets/
├── data/
│   ├── stats.txt
│   └── history.txt
├── docs/
│   ├── 01_wymagania/
│   ├── 02_projekt_i_architektura/
│   ├── 03_testy/
│   └── 04_diagramy_i_harmonogram/
├── reports/coverage/
├── scripts/
├── uruchomienie/
│   ├── 01_URUCHOM_HOSTA.vbs
│   ├── 02_URUCHOM_KLIENTA.vbs
│   ├── 03_URUCHOM_HOSTA_I_KLIENTA.vbs
│   └── README_URUCHOMIENIE.txt
├── tests/
│   ├── unit/
│   ├── whitebox/
│   └── blackbox/
└── README.md
```

---

## 4. Jak uruchomić aplikację

Na Windows aplikację najlepiej uruchamiać przez pliki VBS z folderu `uruchomienie/`.

Najprostszy wariant na jednym komputerze:

1. Otwórz folder `projekt_10_06/`.
2. Wejdź do folderu `uruchomienie/`.
3. Kliknij dwa razy `03_URUCHOM_HOSTA_I_KLIENTA.vbs`.

Ten plik uruchamia osobno panel hosta oraz klienta gracza.

Można też uruchomić aplikację ręcznie w dwóch krokach:

1. `01_URUCHOM_HOSTA.vbs` — uruchamia panel hosta i serwer.
2. `02_URUCHOM_KLIENTA.vbs` — uruchamia klienta gracza.

Najpierw powinien działać host, dopiero potem klient. Po uruchomieniu klienta wybierz grę: **POKER** albo **MAKAO**. W panelu hosta możesz dodać boty lub poczekać na graczy z tej samej sieci LAN, a następnie rozpocząć grę.

Pliki VBS uruchamiają projekt bez widocznego okna `cmd`. Najpierw próbują użyć `pyw -3`, potem `pythonw`, a awaryjnie ukrytego uruchomienia przez `py -3` albo `python`.

Interfejs aplikacji został ustawiony pod format **1920 × 1080**. Jeżeli komputer ma mniejszą rozdzielczość, okno dopasuje się do ekranu, a widok można przewijać w pionie i poziomie, żeby przyciski typu **RAISE** były nadal dostępne.

---

## 5. Jak grać przez LAN

1. Host uruchamia `host_gui.py`.
2. Klient uruchamia `client.py`.
3. Komputery muszą być w tej samej sieci lokalnej.
4. Klient wpisuje adres IP hosta i łączy się z serwerem.
5. Host może uruchomić grę, gdy są gracze albo gdy doda boty.

Domyślny port: **5050**.

---

## 6. Najważniejsze funkcjonalności

### Funkcje ogólne

- wybór gry,
- gra w sieci LAN,
- panel hosta,
- aplikacja klienta,
- chat między graczami,
- zmiana stylu interfejsu,
- wyświetlanie zasad gry,
- lokalne statystyki,
- historia gier.

### Poker

- obsługa faz rozgrywki,
- wirtualne żetony,
- blindy,
- fold/call/raise,
- ocena układów pokerowych,
- showdown,
- rozdzielanie puli,
- bot pokerowy wykorzystujący symulacje Monte Carlo.

### Makao

- rozdawanie i tasowanie kart,
- obsługa kart funkcyjnych,
- dobieranie kart,
- blokowanie tur,
- żądanie koloru i figury,
- mechanizm „Makao”,
- bot do Makao,
- przetasowanie talii, gdy skończą się karty do dobierania.

---

## 7. Architektura w skrócie

Projekt ma podział na warstwy:

1. **Interfejs użytkownika**  
   `client.py`, `host_gui.py`

2. **Logika gier**  
   `poker.py`, `makao.py`

3. **Model danych**  
   `card.py`, `deck.py`, `card_simple.py`, `deck_simple.py`

4. **Boty**  
   `poker_bot.py`, `makao_bot.py`

5. **Komunikacja sieciowa**  
   `socket`, `threading`, wiadomości JSON

6. **Dane lokalne**  
   `stats_manager.py`, folder `data/`

---

## 8. Testy

Projekt zawiera trzy główne typy testów.

### Testy jednostkowe

Obejmują logikę Pokera i Makao.

Uruchomienie:

```bash
python scripts/run_unit_tests.py
```

Aktualny wynik:

```text
Ran 23 tests
OK
```

### Testy białoskrzynkowe

Testy białoskrzynkowe sprawdzają konkretne wewnętrzne ścieżki kodu, m.in. metody pomocnicze, zmiany w `game_state`, efekty kart w Makao, przechodzenie tur w Pokerze oraz zapis statystyk.

Plik z testami:

```text
tests/whitebox/test_whitebox_logic.py
```

Uruchomienie:

```bash
python scripts/run_whitebox_tests.py
```

Aktualny wynik:

```text
Ran 9 tests
OK
```

### Testy czarnoskrzynkowe Pokera

Testy oparte na plikach `.in` i `.out`, które sprawdzają poprawne wyłanianie zwycięzcy i rozdzielanie puli dla różnych układów kart.

Uruchomienie:

```bash
python scripts/run_blackbox_poker.py
```

Aktualny wynik:

```text
Wynik: OK=78, błędne=0, brakujące=0
```

### Wszystkie testy naraz

```bash
python scripts/run_all_tests.py
```

Domyślny runner sprawdza logikę Pokera i Makao, testy białoskrzynkowe oraz testy czarnoskrzynkowe Pokera.

Uwaga: w folderze `tests/unit/` są też testy GUI (`client_test.py`, `host_test.py`). Nie są one uruchamiane w domyślnym skrypcie `run_all_tests.py`, ponieważ wymagają środowiska z działającym ekranem graficznym Tkinter.



---

## 9. Możliwe dalsze rozwijanie projektu

- tryb gry przez Internet, nie tylko LAN,
- logowanie użytkowników,
- ranking graczy,
- zapis rozgrywek w bazie danych,
- lepszy poziom trudności botów,
- instalator aplikacji,
- dalsze rozbudowanie GUI.

---

## 10. Autorzy

Projekt: **Hub z grami Poker i Makao**  
Autorzy wskazani w dokumentacji projektu: **Rafał Koper, Piotr Horodecki, Michał Kostępski**.
