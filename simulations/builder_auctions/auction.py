import random
from formatting import FormatPrinter
import player

class Auction:
    def __init__(self, players, cutoff_time_range):
        self.players = players
        self.cutoff_time_range = cutoff_time_range
        self.player_id_to_player = {p.player_id: p for p in self.players}

    def conduct_round(self):   
        cutoff_time = random.uniform(self.cutoff_time_range[0], self.cutoff_time_range[1])

        # Step 1: All players generate valuation and submit time
        submit_times = []
        for p in self.players:
            val, submit_by = p.generate_round_info()
            submit_times.append(submit_by)

        # Step 2: Determine strategies for each player
        strategies = {}
        for i, p in enumerate(self.players):
            if isinstance(p, player.ReactiveGaussianRangePlayer):
                # Provide submit_by of all other players
                others_submit_by = [submit_times[j] for j in range(len(self.players)) if j != i]
                strategies[p.player_id] = p.determine_strategy(others_submit_by, cutoff_time)
            else:
                strategies[p.player_id] = p.determine_strategy()

        # Step 3: Filter bids submitted before cutoff and sort by time
        bid_order = sorted(
            [(p_id, strategy[2]) for p_id, strategy in strategies.items() if strategy[2] < cutoff_time],
            key=lambda x: x[1]
        )

        winner = None
        winning_bid = None
        winning_value = None

        if len(bid_order) == 0:
            winner = None
        elif len(bid_order) == 1:
            winner = bid_order[0][0]
        else:
            # Select highest bid among all
            highest_bid = -1
            for pid, _ in bid_order:
                bid_amount = strategies[pid][1]
                if bid_amount > highest_bid:
                    highest_bid = bid_amount
                    winner = pid

        if winner is not None:
            winning_bid = strategies[winner][1]
            winner_player = self.player_id_to_player[winner]
            winning_value = winner_player.val - winning_bid

        round_data = {
            "valuations": [p.val for p in self.players],
            "strategies": strategies,
            "cutoff_time": cutoff_time,
            "bid_order": bid_order,
            "winner": (winner, winning_bid, winning_value) if winner is not None else None
        }
        return round_data

    def run_simulation(self, num_rounds):
        results = []
        winnings = [0.0] * len(self.players)

        # Create mapping from player_id to index in list
        pid_to_index = {p.player_id: i for i, p in enumerate(self.players)}

        for _ in range(num_rounds):
            round_data = self.conduct_round()
            winner = round_data["winner"]
            if winner:
                pid, _, profit = winner
                winnings[pid_to_index[pid]] += profit
            results.append(round_data)

        return results, winnings

    def get_results(self):
        return self.round_results