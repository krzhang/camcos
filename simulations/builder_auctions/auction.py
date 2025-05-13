import random
from formatting import FormatPrinter
import player

class Auction:
    def __init__(self, players, cutoff_time_range):
        self.players = players
        self.cutoff_time_range = cutoff_time_range

    def generate_round_info(self,debug=False):
        """
        Placeholder for generating the information the player gets that might be unique to the
        round. Specifically, return vals of valuations and submit_bys of submit_by's,
        where:

        [valuation]: the reward for winning the block for the player
        [submit_by]: the time in [0,1] that the player must submit by (due to the player's own
        latency for that round; it might still be possible that the player fails to successfully
        submit that round given future randomness)
        """

        vals = {}
        submit_bys = {}

        for p in self.players:
            pid = p.player_id
            vals[pid] = random.uniform(0.0, 1.0)  # Example: Random valuation between 0 and 1
            submit_bys[pid] = random.uniform(p.speed[0], p.speed[1]) # the time the speed forces you to submit by
            if debug:
                print("ID: {} Val: {} submit_by: {}".format(pid, vals[pid], submit_bys[pid]))

        return (vals, submit_bys)

    def conduct_round(self, debug=False):   
        """
        Logic of conducting a round:

        1) all players, based on some speed, determine when they submit 
        2) in order of when they submit, we ask them for their actions; they are then allowed
           to use the information of the bids they have seen but also the knowledge of players
           they have not seen
        3) we also roll for a cutoff time (for example, if the cutoff time is 0.9, then all bids
           after 0.9 are destroyed). We need this for some of the phenomena
        """
        cutoff_time = random.uniform(self.cutoff_time_range[0], self.cutoff_time_range[1])
        if debug:
            print("Cutoff time: {}".format(cutoff_time))
        # Step 1: generate valuation and submit time
    
        vals, submit_bys = self.generate_round_info(debug=debug)
        # real_val = random.uniform(0.7, 1.0)  # True MEV realized when block is built

        submit_order = sorted(
            [p for p in self.players],
            key=lambda x: submit_bys[x.player_id])
        # this gives a list of the players in action order

        # Step 2: Determine strategies for each player
        actions = []
        winner = None
        winning_bid = 0
        winning_value = None
        for p in submit_order:
            bid = p.determine_bid(vals[p.player_id], self, actions, debug=debug)
            actions.append((p, bid))
            if bid > winning_bid:
                winner = p
                winning_bid = bid

        if winner is not None:
            # winning_value = real_val - winning_bid
            winning_value = vals[winner.player_id] - winning_bid

        round_data = {
            "valuations": vals,
            "submit_bys": submit_bys,
            "actions": actions,
            "cutoff_time": cutoff_time,
            "submit_order": submit_order,
            "winning_bid": winning_bid,
            # "real_val": real_val,
            "winner": (winner.player_id, winning_bid, winning_value) if winner is not None else None
        }
        return round_data

    def run_simulation(self, num_rounds, debug=False):
        results = []
        winnings = [0.0] * len(self.players)

        # Create mapping from player_id to index in list
        pid_to_index = {p.player_id: i for i, p in enumerate(self.players)}

        for _ in range(num_rounds):
            round_data = self.conduct_round(debug=debug)
            winner = round_data["winner"]
            if winner:
                pid, _, profit = winner
                winnings[pid_to_index[pid]] += profit
                if debug:
                    print ("{} won {}".format(pid, profit))
            results.append(round_data)

        return results, winnings

    def get_results(self):
        return self.round_results