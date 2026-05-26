from card import Card
import random

class Deck:
    def __init__(self, deck_number=1):
        self.cards = []

        suits = ["hearts", "spades", "diamonds", "clubs"]
        faces = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

        for i in range(deck_number):
            for suit in suits:
                for face in faces:
                    self.cards.append(Card(suit, face))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()