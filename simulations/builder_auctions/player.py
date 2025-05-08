import random

EPSILON = 0.001

WAIT_AND_UNDERBID_IF_ABLE = 0 # right now this is the only "strategy code" but this can change

class Player:
    # should make more classes, but for now
  
    def __init__(self, player_id, speed):
        self.player_id = player_id
        self.speed = speed
        # valuation
        # speed 

    def generate_round_info(self):
        """
        Placeholder for generating the information the player gets that might be unique to the
        round.
        Replace with actual logic.
        """
        val = random.uniform(0.0, 1.0)  # Example: Random valuation between 0 and 100
        submit_by = random.uniform(self.speed[0], self.speed[1]) # the time the speed forces you to submit by
        self.val = val
        self.submit_by = submit_by
        return (val, submit_by)
      
    def determine_strategy(self):
        """
        Placeholder for determining the strategy based on valuation and internal parameters.
        Replace with actual logic.

        Assume generate_round_info() was already called.
        """
        # in the simplest case, bid the valuation at a discount by the submit_by time, or underbid
        # the 
        return (WAIT_AND_UNDERBID_IF_ABLE, self.val/2, self.submit_by)

class NaivePlayer(Player):

    def determine_strategy(self):
        """
        This player just opens with a bid immediately.
        """
        return (WAIT_AND_UNDERBID_IF_ABLE, self.val/2, 0.0)

class BluffPlayer(Player):

    def determine_strategy(self):
        """
        This player will bluff with some probability.
        """ 
        if random.uniform(0,1) < 0.1:
            # in the future, probably should depend on other factors
            return (WAIT_AND_UNDERBID_IF_ABLE, EPSILON, self.submit_by)
        else:
            return (WAIT_AND_UNDERBID_IF_ABLE, self.val/2, self.submit_by)

class GaussianRangePlayer(Player):
    """ As requested, a player with some range of scaling of their bids. """

    def __init__(self, player_id, speed, range):
        """ 
        example range: [0.75, 0.33] for mean/variance. The range is to be multiplied
        with the evaluation.
        """
        self.player_id = player_id
        self.speed = speed 
        self.range = range

    def determine_strategy(self):
        """
        Unlike the naive self.val/2, this player will take the valuations and then
        scale by something in the range... of course, the player will not overbid 
        the valuation.
        """
        bid_prop = min(max(0.5,random.gauss(self.range[0], self.range[1])), 1-EPSILON)
        return (WAIT_AND_UNDERBID_IF_ABLE, bid_prop * self.val, self.submit_by)
    
class ReactiveGaussianRangePlayer(Player):
    """ 
    A player that reacts based on whether it sees p1's bid.
    """

    def __init__(self, player_id, speed, range, others_range):
        self.player_id = player_id
        self.speed = speed
        self.range = range
        self.others_range = others_range

    def determine_strategy(self, others_submit_by, cutoff_time):
        """
        Reacts based on whether the player sees earlier bids from any other players.
        """
        bid_prop_self = min(max(0.5,random.gauss(self.range[0], self.range[1])), 1-EPSILON)
        original_bid = bid_prop_self * self.val

        guessed_bids = []

        for other_submit_by in others_submit_by:
            if other_submit_by < self.submit_by < cutoff_time:
                guessed_other_prop = min(max(0.5, random.gauss(self.others_range[0], self.others_range[1])), 1-EPSILON)
                guessed_other_bid = guessed_other_prop * self.val
                guessed_bids.append(guessed_other_bid)
            else:
                guessed_bids.append(0)  # Didn't see this player's bid

        max_guess = max(guessed_bids)

        if original_bid < max_guess < self.val:
            adjusted_bid = max_guess
        elif max_guess < original_bid:                    # choice to hide this; dampen bid case
            adjusted_bid = (max_guess + original_bid) / 2
        else:
            adjusted_bid = original_bid

        return (WAIT_AND_UNDERBID_IF_ABLE, adjusted_bid, self.submit_by)