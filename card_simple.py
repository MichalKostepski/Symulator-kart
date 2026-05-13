class CardSimple:
    def __init__(self, suit, face):
        self.suit = suit
        self.face = face

    def __str__(self):
        return f"{self.face}{self.suit}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, CardSimple):
            return False

        return (
            self.face == other.face and
            self.suit == other.suit
        )

    def __hash__(self):
        return hash((self.face, self.suit))