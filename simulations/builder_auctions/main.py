import random
from formatting import FormatPrinter
from player import Player
import numpy as np

class Auction:
    def __init__(self, players):
        self.players = players
        assert len(players) == 2 # support more players later

    def conduct_round(self):
        round_infos = {player.player_id: player.generate_round_info() for player in self.players}
        # pairs of (val, submit_by)
        
        strategies = {player.player_id: player.determine_strategy() for player in self.players}

        cutoff_time = random.uniform(0.7, 1.0) # when this simulator actually stops taking bids
        
        # determining the winner and price logic

        bid_order = sorted([(i, strategies[i][2]) for i in range(len(self.players))
                            if strategies[i][2] < cutoff_time],
                           key = lambda x: x[1])
        # (bidder, time) for time that's eligible.

        winning_bid = None
        winning_value = None

        if len(bid_order) == 0:
            winner = None
            winning_bid = None
        else:
            if len(bid_order) == 1:
                winner = bid_order[0][0]
                winning_bid = strategies[winner][1] 
            else:
                assert len(bid_order) == 2
                first_player = bid_order[0][0]
                second_player = bid_order[1][0]
                first_bid_amount = self.players[first_player].val * strategies[first_player][1]
                second_bid_amount = self.players[second_player].val * strategies[second_player][1]
                if second_bid_amount > first_bid_amount:
                    winner = second_player
                else:
                    winner = first_player

            winning_bid = self.players[winner].val * strategies[winner][1]
            winning_value = self.players[winner].val - winning_bid


        
        # Collect round data
        round_data = {
            "valuations": [p.val for p in self.players],
            "strategies": strategies,
            "cutoff_time": cutoff_time,
            "bid_order": bid_order,
            "winner": (winner, winning_bid, winning_value) if winner is not None else None
        }
        return round_data

    def run_simulation(self, num_rounds):
        round_results = []
        winnings = [0.0, 0.0]
        for _ in range(num_rounds):
            round_data = self.conduct_round()
            if round_data["winner"] is not None and round_data["winner"][0] is not None:
                w = round_data["winner"][0]
                winnings[w] += round_data["winner"][2]
            round_results.append(round_data)
        return (round_results, winnings)

    def get_results(self):
        return self.round_results

# Example usage
def test(num_rounds):
    speeds = [1.0, 1.0] # same for now...
    players = [Player(player_id=i, speed=speeds[i]) for i in range(2)]
    auction = Auction(players)
    round_results, winnings = auction.run_simulation(num_rounds)

    for i, result in enumerate(round_results, start=1):
        print(f"Round {i}")
        FormatPrinter({float: "%.4f"}).pprint(result)
        # from [python - pprint with custom float formats - Stack Overflow](https://stackoverflow.com/questions/44356693/pprint-with-custom-float-formats)
        print("\n")
    
    print(f"Winnings: {winnings}")

import main; main.test(1000)



