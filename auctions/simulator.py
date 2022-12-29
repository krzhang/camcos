import numpy as np
import scipy as sp

class Distribution(object):
  """
  A thin wrapper to sample from a distribution.
  """
  def sample(self, k):
    """ return k samples, in a list"""
    pass

  def nash(self, k, value):
    """ given a valuation, how to bid when there are k players?"""
    pass

class UniformDistribution(Distribution):
  def __init__(self, low, high):
    self.low = low
    self.high = high

  def __str__(self):
    return "uniform"
    
  def sample(self, k):
    return np.random.uniform(self.low, self.high, k)

  def nash(self, k, value):
    integral = sp.integrate.quad(lambda x: pow((x-self.low)/(value - self.low + 0.000000001), k-1), self.low + 0.0000000001, value)
    return value - integral[0]
  
class GammaDistribution(Distribution):
  def __init__(self, shape, scale):
    self.shape = shape
    self.scale = scale

  def __str__(self):
    return "gamma"
    
  def sample(self, k):
    return np.random.gamma(self.shape, self.scale, k)

  def nash(self, k, value):
    cdf = lambda x: sp.stats.gamma.cdf(x, self.shape, scale=self.scale)
    integral = sp.integrate.quad(lambda x: pow(cdf(x)/cdf(value), k-1), 0, value)
    return value - integral[0]

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

  def simulate_single_turn(self):
    """ simulate a single turn, returning all relevant data"""
    valuations = self.distribution.sample(self.num_agents)
    bids = [self.distribution.nash(self.num_agents, s) for s in valuations]
    winning_index = np.argmax(bids)
    revenue = bids[winning_index]
    winner_gain = valuations[winning_index] - revenue
    return (valuations, bids, revenue, winner_gain)

  def simulate_turns(self, k, as_percentile=95):
    data = [self.simulate_single_turn() for i in range(k)]
    revenues = [d[2] for d in data]
    average_bid = np.average([np.average(d[1]) for d in data])
    # auction-smashing bid
    ASB = np.percentile(revenues, as_percentile)
    ASP = ASB - average_bid
    winner_gains = [d[3] for d in data]
    print("{} {} agents".format(self.num_agents, self.distribution))
    print("average revenue: {}".format(sum(revenues)/k))
    print("average gains: {}".format(sum(winner_gains)/k))
    print("average bid: {}".format(average_bid))
    print("ASB: {}".format(ASB))
    print("ASP: {}".format(ASP))
    return data
