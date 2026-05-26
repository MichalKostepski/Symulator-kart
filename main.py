from deck import Deck
from player import Player
import random

deck = Deck()
deck.shuffle()

pot = 0

# liczba graczy
n = 4

player_list = []
for i in range(n):
    player = Player()
    player_list.append(player)

# dealer (losowany na start)
dealer = random.randint(0, n - 1)

# jeden blind
blind = (dealer + 1) % n

# gracz zaczynający (po blindzie)
start_player = (blind + 1) % n


while True:
    print("1. Zagraj rundę")
    print("2. Pokaż wyniki")
    print("3. Wyjdź")

    choice = input("Wybierz opcję: ")

    if choice == "1":
        # uruchom rundę
        pass
    elif choice == "2":
        # pokaż wyniki
        pass
    elif choice == "3":
        break
    else:
        print("Nieprawidłowa opcja")