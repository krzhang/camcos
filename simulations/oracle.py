import pandas as pd
from collections import deque

DEFAULT_ORACLE_INDEX = 60 # current geth oracle looks at the 60th smallest 

def load_data(filename):
  """
  read in data from a CSV to create the right context for simulations. Return as DataFrame.
  """
  data = pd.read_csv(filename)
  df = data[['gasLimit', 'minGasPrice']]
  return df

class Oracle():

  def __init__(self, filename="block_data.csv"):
    """ 
    read in data to initialize oracle. The main object is [block_mins], a list of block minimums
    for future oracle updates.
    """
    self.block_mins = deque([])
    # the main oracle object, storing the block minimums (min price needed to get in block)
    # (keep sorted) TODO: use a heap
    self.oracle_index = 60 # the oracle price is the 60th price in the sorted block mins
    data = load_data(filename)
    self.initialize_from_data(data)

  def initialize_from_data(self, data):
    df = data.values 
    for d in df:
      if len(self.block_mins) == 100:
        break
      if d[1] == 'None':
        continue
      self.block_mins.append(int(d[1]) / 10**9) # divide to convert Gwei
      
  def price(self, bfvalue):
    sorted_mins = sorted([x - bfvalue if x >= bfvalue else 0 for x in self.block_mins])
    return sorted_mins[self.oracle_index - 1]
      
  def update(self, block):
    """ given a block, how to update the oracle?"""
    recent_gp = block[-1][1]
    self.block_mins.popleft()
    self.block_mins.append(recent_gp)

class MultiOracle():

  def __init__(self, dimensions, filename="block_data.csv"):
    """ 
    read in data to initialize oracle. Needs to return a [block_mins] list of block minimums
    for future oracle updates.
    """
    super().__init__(filename)
    self.block_mins = deque([])
    # the main oracle object, storing the block minimums (min price needed to get in block)
    # (keep sorted) TODO: use a heap
    self.oracle_index = 60 # the oracle price is the 60th price in the sorted block mins
    
    data = pd.read_csv(filename)
    df = data[['gasLimit','minGasPrice']].values 
    for d in df:
      if len(self.block_mins) == 100:
        break
      if d[1] == 'None':
        continue
      self.block_mins.append(int(d[1]) / 10**9) # divide to convert Gwei

  def price(self, bfvalue):
    sorted_mins = sorted([x - bfvalue if x >= bfvalue else 0 for x in self.block_mins])
    return sorted_mins[self.oracle_index - 1]
      
  def update(self, block):
    """ given a block, how to update the oracle?"""
    recent_gp = block[-1][1]
    self.block_mins.popleft()
    self.block_mins.append(recent_gp)
