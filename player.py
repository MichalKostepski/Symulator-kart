class Player:
    def __init__(self):
        self.hand = []
        self.coins = 100
        self.bet = 0
    def draw_one (self, card):
        self.hand.append(card) 
