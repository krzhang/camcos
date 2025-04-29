import random

EPSILON = 0.000001

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
        val = random.uniform(0.7, 0.9)  # Example: Random valuation between 0 and 100
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
        bid_prop = min(random.gauss(self.range[0], self.range[1]), 1)
        return (WAIT_AND_UNDERBID_IF_ABLE, bid_prop * self.val, self.submit_by)
    
class ReactiveGaussianRangePlayer(Player):
    """ 
    A player that reacts based on whether it sees p1's bid.
    """

    def __init__(self, player_id, speed, range, p1_range):
        self.player_id = player_id
        self.speed = speed
        self.range = range
        self.p1_range = p1_range

    def determine_strategy(self, p1_submit_by, cutoff_time):
        """
        If p2 sees p1's bid (based on submit_by timing),
        p2 adjusts its own bid accordingly.
        """
        bid_prop_p2 = min(random.gauss(self.range[0], self.range[1]), 1)
        original_bid_p2 = bid_prop_p2 * self.val

        if self.submit_by > p1_submit_by and p1_submit_by < cutoff_time:
            # p2 sees p1's bid and reacts
            guessed_p1_prop = min(random.gauss(self.p1_range[0], self.p1_range[1]), 1)
            guessed_p1_bid = guessed_p1_prop * self.val  # p2 uses its own valuation to guess

            # if p2 guesses p1 will take win the block, and is still profitable, change p2 bid to overtake
            if self.val > guessed_p1_bid > original_bid_p2:
                final_bid = guessed_p1_bid
            # if p2 guesses p1 will overly overbid, stay reserved
            elif guessed_p1_bid > self.val:
                final_bid = 0.8 * original_bid_p2
            # if p2 guesses p1 will underbid, soften p2 bid to gain more profit (is in assumption they win)
            else:
                final_bid = (guessed_p1_bid + original_bid_p2)/2
            
            return (WAIT_AND_UNDERBID_IF_ABLE, final_bid, self.submit_by)

        else:
            # p2 doesn't see p1 then bid normal
            return (WAIT_AND_UNDERBID_IF_ABLE, original_bid_p2, self.submit_by)
        