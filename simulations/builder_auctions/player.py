import random
from scipy.stats import truncnorm


EPSILON = 0.000001

WAIT_AND_UNDERBID_IF_ABLE = 0 # right now this is the only "strategy code" but this can change

class Player:
    # should make more classes, but for now
  
    def __init__(self, player_id, speed, bid_percentage):
        self.player_id = player_id
        self.speed = speed
        self.bid_percentage = bid_percentage
        # valuation
        # speed 

class Player:
    def __init__(self, player_id, speed, bid_percentage):
        self.player_id = player_id
        self.speed = speed
        self.bid_percentage = bid_percentage


    def generate_round_info(self):
        self.val = random.uniform(0,1)
        self.submit_by = random.uniform(0, self.speed)
        bid_mean, bid_std = 0.75, 0.329

        a = (0 - bid_mean) / bid_std
        b = (1 - bid_mean) / bid_std

        self.bid_percentage = float(truncnorm.rvs(a, b, loc = bid_mean, scale = bid_std))
        self.bid = self.val * self.bid_percentage

        return (self.val, self.submit_by)

    def determine_strategy(self):
        return (WAIT_AND_UNDERBID_IF_ABLE, self.bid, self.submit_by)

class FastPlayer(Player):
    
    def determine_strategy(self):

        return (WAIT_AND_UNDERBID_IF_ABLE, self.bid, self.submit_by)

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
