import random

EPSILON = 0.00001
class Player:
    # should make more classes, but for now
  
    def __init__(self, player_id, speed):
        """
        [speed]: (lower_bound, upper_bound) determines when a player bids; higher speed is better
        and means they can submit later in a round.
        """
        self.player_id = player_id
        self.speed = speed

    def determine_bid(self, val, auction, actions):
        """
        Placeholder for determining the bid based on valuation and internal parameters.
        Replace with actual logic.

        Assume generate_round_info() was already called.

        val: the valuation
        auction: the Auction object
        actions: a list of actions of form (player, bid). 
        """
        return None

class NaivePlayer(Player):

    def __init__(self, player_id, speed, val_discount=0.5):
        self.val_discount = val_discount
        super().__init__(player_id, speed)

    def determine_bid(self, val, auction, actions):
        """
        This player just opens with a bid.
        """
        return val*self.val_discount

class RangePlayer(Player):
    """ 
    [reactive]: a bool of whether or not it sees the other bids.
    """

    def __init__(self, player_id, speed, range, reactive):
        self.player_id = player_id
        self.speed = speed
        self.range = range
        self.reactive = reactive

    def sample_naive_bid_ratio(self):
        """
        Used for 2 things:
        1) for a naive Rangeplayer to sample a bid (non-reactive)
        2) for another Rangeplayer to sample your bid (when predicting)
        """
        low = self.range[0] - self.range[1]
        high = self.range[0] + self.range[1]
        return min(max(0, random.uniform(low, high)), 1-EPSILON)
        # bid_prop_self = min(max(0, random.gauss(self.range[0], self.range[1])), 1-EPSILON)

    def determine_bid(self, val, auction, actions, debug=False):
        """
        Reacts based on whether the player sees earlier bids from any other players.
        """

        my_bid = self.sample_naive_bid_ratio() * val

        if debug:
            print("{} bid: {}".format(self.player_id, my_bid))

        if (not self.reactive):
            return my_bid

        # now we must adjust for other bids.
        # 1) since we have seen actions so far, we should at least overbid the actions we have 
        #    seen (if it's valuable to us)
        # 2) for players we have not seen, we should sample their bid (for the future, possibly
        #    multiple times) as a proxy to their bid

        seen = [] # list of players we have seen 
        for (p, bid) in actions:
            pid = p.player_id
            if debug:
                if auction.sealed_bids:
                    print ("Sees {} bid some value".format(pid))
                else:
                    print ("Sees {} bid {}".format(pid, bid))
            seen.append(pid)
            if auction.sealed_bids:
                bid = p.sample_naive_bid_ratio() * random.uniform(0.0, 1.0) 
                if val > bid >= my_bid:
                    my_bid = min(bid + EPSILON, val)
                    if debug:
                        print("{} considers updating bid to {} due to: {}".format(self.player_id, my_bid, pid))
            else:
                if val > bid >= my_bid:
                    my_bid = min(bid + EPSILON, val)
                    if debug:
                        print("{} considers updating bid to {} due to: {}".format(self.player_id, my_bid, pid))

        for p in auction.players:
            if p.player_id not in seen and p.player_id != self.player_id:
                # we haven't seen this player yet, so just sample
                # for future: can consider some sort of dampening
                if debug:
                    print("considers {}".format(p.player_id))
                bid = p.sample_naive_bid_ratio() * random.uniform(0.0, 1.0) 
                if val > bid >= my_bid:
                    if debug:
                        print("{} considers updating bid to {} due to: not seeing bid from {}".format(self.player_id, my_bid, p.player_id))
                    my_bid = min(bid, val)

        if debug:
            print("{} bids {}".format(self.player_id, my_bid))
        return my_bid