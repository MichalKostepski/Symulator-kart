import random


class PokerBot:



    DEFAULT_SIMULATIONS = 400

    def __init__(self, game, player_id, simulations=DEFAULT_SIMULATIONS):
        self.game = game
        self.player_id = player_id
        self.simulations = simulations





    def get_move(self):
        state = self.game.game_state

        current_bet = state["current_bet"]
        my_bet = state["round_bets"].get(self.player_id, 0)
        chips = state["chips"].get(self.player_id, 0)
        amount_to_call = max(0, current_bet - my_bet)
        pot = state["pot"]

        if chips <= 0:
            return {"action": "CALL"}


        equity = self.estimate_equity()




        if amount_to_call > 0:
            pot_odds = amount_to_call / (pot + amount_to_call)
        else:
            pot_odds = 0

        print(
            f"[POKER BOT MC] Bot {self.player_id}: "
            f"equity={equity:.3f}, pot_odds={pot_odds:.3f}, "
            f"to_call={amount_to_call}, chips={chips}, phase={state['phase']}"
        )



        if amount_to_call > chips:
            return {"action": "FOLD"}


        if amount_to_call == 0:

            if equity >= 0.62 and self.can_raise():
                return self.build_raise(equity)
            return {"action": "CALL"}


        if equity >= 0.70 and self.can_raise():
            return self.build_raise(equity)



        safety_margin = 0.05
        if equity >= pot_odds + safety_margin:
            return {"action": "CALL"}



        if amount_to_call <= state["blind_amount"] and equity >= 0.25:
            return {"action": "CALL"}

        return {"action": "FOLD"}





    def estimate_equity(self):
        state = self.game.game_state
        my_hand = list(state["hands"].get(self.player_id, []))
        community = list(state["community_cards"])

        if len(my_hand) < 2:
            return 0.0

        opponents = self.get_active_opponents()


        if not opponents:
            return 1.0

        wins = 0
        ties = 0
        completed_simulations = 0

        for _ in range(self.simulations):
            deck = self.build_unknown_deck(my_hand, community)

            needed_cards = len(opponents) * 2 + (5 - len(community))
            if len(deck) < needed_cards:
                break

            random.shuffle(deck)

            index = 0
            simulated_opponent_hands = []

            for _opponent_id in opponents:
                opponent_hand = [deck[index], deck[index + 1]]
                simulated_opponent_hands.append(opponent_hand)
                index += 2

            simulated_community = community + deck[index:index + (5 - len(community))]

            my_score, _ = self.game.get_best_hand(my_hand + simulated_community)
            opponent_scores = []

            for opponent_hand in simulated_opponent_hands:
                opponent_score, _ = self.game.get_best_hand(opponent_hand + simulated_community)
                opponent_scores.append(opponent_score)

            best_opponent_score = max(opponent_scores)

            if my_score > best_opponent_score:
                wins += 1
            elif my_score == best_opponent_score:



                tied_opponents = sum(1 for score in opponent_scores if score == my_score)
                ties += 1 / (tied_opponents + 1)

            completed_simulations += 1

        if completed_simulations == 0:
            return 0.0

        return (wins + ties) / completed_simulations

    def build_unknown_deck(self, my_hand, community):
        suits = ["hearts", "spades", "diamonds", "clubs"]
        faces = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

        full_deck = [f"{face} of {suit}" for suit in suits for face in faces]

        known_cards = set()
        for card in my_hand + community:
            known_cards.add(self.normalize_card(card))

        return [card for card in full_deck if self.normalize_card(card) not in known_cards]

    def normalize_card(self, card):
        return self.game.parse_card(card)

    def get_active_opponents(self):
        state = self.game.game_state
        folded = state["folded_players"]
        opponents = []

        for player_id, _conn, _addr in self.game.players:
            if player_id == self.player_id:
                continue
            if player_id in folded:
                continue
            if player_id not in state["hands"]:
                continue
            opponents.append(player_id)

        return opponents





    def can_raise(self):
        state = self.game.game_state
        current_bet = state["current_bet"]
        my_bet = state["round_bets"].get(self.player_id, 0)
        chips = state["chips"].get(self.player_id, 0)

        return my_bet + chips > current_bet

    def build_raise(self, equity):
        state = self.game.game_state

        current_bet = state["current_bet"]
        my_bet = state["round_bets"].get(self.player_id, 0)
        chips = state["chips"].get(self.player_id, 0)
        blind = state["blind_amount"]


        if equity >= 0.85:
            raise_step = blind * 5
        elif equity >= 0.75:
            raise_step = blind * 3
        else:
            raise_step = blind * 2

        raise_step = max(raise_step, 20)
        raise_to = current_bet + raise_step

        max_possible_bet = my_bet + chips
        raise_to = min(raise_to, max_possible_bet)

        if raise_to > current_bet:
            return {
                "action": "RAISE",
                "amount": raise_to
            }

        return {"action": "CALL"}

    def create_move_message(self):
        move = self.get_move()
        return self.game.create_msg(
            game="POKER",
            msg_type="MOVE",
            player_id=self.player_id,
            data=move
        )
