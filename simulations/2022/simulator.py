import numpy as np
import pandas as pd
import random

from collections import deque

DEFAULT_ORACLE_INDEX = 60 # current geth oracle looks at the 60th smallest 

class Basefee():

  def __init__(self, d, target_limit, max_limit):
    self.target_limit = target_limit
    self.max_limit = max_limit
    self.d = d
    self.value = 0.0

  def update(self, gas):
    """ return updated basefee given [b] original basefee and [g] gas used"""
    self.value = self.value*(1+self.d*((gas-self.target_limit)/self.target_limit))

class Simulator():

  def __init__(self):
    self.blocks = []
    self.block_mins = deque([])
    self.gas_price_batches = []
    self.wait_times = []
    self.mempool = pd.DataFrame()
    
  def simulate(self, n):
    """ Simulate for n steps """
    pass 

class BasefeeSimulator(Simulator):

  """ Default 'Post-EIP-1559' or I guess now 'standard' simulator. """

  def __init__(self, basefee):
    self.basefee = basefee
    self.current_oracle = 0.0
    super().__init__()
  
  def update_mempool(self, txn_count, t=0):
    """
    Make [txn_number] new transactions and add them to the mempool
    """
    # the valuations and gas limits for the transactions. Following code from
    # 2021S
    valuations = np.random.gamma(20.72054, 1/17.49951, txn_count)
    gas_prices = [self.basefee.value + (self.current_oracle * v)
                  for v in valuations]
    self.gas_price_batches += [gas_prices]

    gas_limits = (np.random.pareto(1.42150, txn_count)+1)*21000
    # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
    
    # store each updated mempool as a DataFrame

    self.mempool = pd.concat([self.mempool, pd.DataFrame({
        'gas price': gas_prices,
        'gas limit': gas_limits,
        'time': t,
        'amount paid': [x * y for x,y in zip(gas_prices, gas_limits)]})], ignore_index=True)
    
    # sort transactions in each mempool by gas price
    
    self.mempool = self.mempool.sort_values(by=['gas price'], ascending=False).reset_index(drop=True)
    return
  
  def update_oracle(self):
    recent_gp = self.blocks[-1][-1][1]
    self.block_mins.popleft()
    self.block_mins.append(recent_gp)

    sorted_block_mins = sorted(self.block_mins)
    self.current_oracle = sorted_block_mins[DEFAULT_ORACLE_INDEX-1]

  def fill_block(self, time):
    """ create a block greedily from the mempool and return it"""
    block = []
    block_size = 0
    block_limit = self.basefee.max_limit

    for i in range(len(self.mempool)):
      txn = self.mempool.iloc[i, :].tolist()
      if block_size + txn[1] > block_limit or txn[0] < self.basefee.value:
        break
      else:
        block.append(txn)
        block_size += txn[1]

    block_wait_times = [time - txn[2] for txn in block]
    self.wait_times.append(block_wait_times)

    self.mempool = self.mempool.iloc[i+1: , :]
    return block, block_size

  def simulate(self, step_count, init_txns=8500, txns_per_turn=200):
    """ Run the simulation for n steps """

    # initialize empty dataframes
    block_data = pd.DataFrame()
    mempool_data = pd.DataFrame()
    mempools = []
    mempools_bf = []
    txn_counts = []

    #read in data to initialize oracle
    data = pd.read_csv('block_data.csv')
    minGasdf = data[['gasLimit','minGasPrice']].values 
    for d in minGasdf:
      if len(self.block_mins) == 100:
        break
      if d[1] == 'None':
        continue
      self.block_mins.append(int(d[1]) / 10**9) # divide to convert Gwei

    self.basefee.value = self.block_mins[-1]
    basefees = [self.basefee.value]

    sorted_block_mins = sorted([x - self.basefee.value if x >= self.basefee.value
                                else 0 for x in self.block_mins])

    #set initial oracles
    self.current_oracle = sorted_block_mins[DEFAULT_ORACLE_INDEX-1]

    #initialize mempools 
    self.update_mempool(init_txns)

    #iterate over n blocks
    for i in range(step_count):
      #fill blocks from mempools
      new_block, new_block_size = self.fill_block(i)
      self.blocks += [new_block]
      self.update_oracle()

      #update mempools

      self.basefee.update(new_block_size)
      basefees += [self.basefee.value]

      mempools += [pd.DataFrame(self.mempool)]
      # this creates a copy; dataframes and lists are mutable
      mempools_bf += [self.mempool[self.mempool['gas price'] >= self.basefee.value]]
      # what does this do??

      # add 200 new txns before next iteration
      new_txns_count = random.randint(50, txns_per_turn*2 - 50)
      self.update_mempool(new_txns_count, i)

      txn_counts += [new_txns_count]

      # print("progress: ", i+1, end = '\r')
    return basefees, self.blocks, mempools, mempools_bf, txn_counts, self.wait_times
