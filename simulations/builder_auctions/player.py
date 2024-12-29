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
        val = random.uniform(0, 1)  # Example: Random valuation between 0 and 100
        submit_by = random.uniform(0, self.speed) # the time the speed forces you to submit by
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
