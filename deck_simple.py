from card_simple import CardSimple
import random


class DeckSimple:

    def __init__(self, deck_number=1):
        self.cards = []

        suits = ["H", "S", "D", "C"]
        faces = ["2", "3", "4", "5", "6", "7",
                 "8", "9", "T", "J", "Q", "K", "A"]

        for _ in range(deck_number):
            for suit in suits:
                for face in faces:
                    self.cards.append(CardSimple(suit, face))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if len(self.cards) == 0:
            return None

        return self.cards.pop()

    def add_card(self, card):
        self.cards.append(card)

    def add_cards(self, cards):
        self.cards.extend(cards)

    def size(self):
        return len(self.cards)

    def is_empty(self):
        return len(self.cards) == 0

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return f"Deck({len(self.cards)} cards)"