import numpy

class Agent(object):
  """
  A single agent, which is characterized by a distribution.
  """
  pass

class Simulator(object):
  """
  A simulator for one auction.
  """

  def __init__(self):
    pass

  def simulate_turn(self):
    pass

class SymmetricSimulator(Simulator):
  """
  Each agent has the same distribution.
  """

  def __init__(self, num_agents, distribution):
    self.num_agents = num_agents
    self.distribution = distribution

  def simulate_turn(self):
    valuations = [self.sample_signal(self.distribution) for i in range(self.num_agents)]
    bids = [self.sample_bid(s) for s in valuations]
    winning_index = numpy.argmax(bids)
    revenue = bids[winning_index]
    winner_gain = valuations[winning_index] - revenue
    return (valuations, bids, revenue, winner_gain)
