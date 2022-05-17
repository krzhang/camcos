import numpy as np
import pandas as pd
import random

from collections import deque

DEFAULT_ORACLE_INDEX = 60 # current geth oracle looks at the 60th smallest 

class Oracle():

  def __init__(self, filename="block_data.csv"):
    """ 
    read in data to initialize oracle. Needs to return a [block_mins] list of block minimums
    for future oracle updates.
    """
    self.block_mins = deque([])
    # the main oracle object, storing the block minimums (min price needed to get in block)
    # (keep sorted) TODO: use a heap
    self.oracle_index = 60 # the oracle price is the 60th price in the sorted block mins
    self.current_oracle_price = None # the current oracle price
    
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

class Basefee():

  def __init__(self, d, target_limit, max_limit, value=0.0):
    self.target_limit = target_limit
    self.max_limit = max_limit
    self.d = d
    self.value = value

  def scaled_copy(self, ratio):
    """ gives a scaled copy of the same basefee objects; think of it as a decominator change """
    return Basefee(self.d, self.target_limit*ratio, self.max_limit*ratio, self.value*ratio)

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
    super().__init__()
    self.basefee = basefee
    # self.current_oracle = 0.0
  
  def update_mempool(self, txn_count, t=0):
    """
    Make [txn_number] new transactions and add them to the mempool
    """
    # the valuations and gas limits for the transactions. Following code from
    # 2021S
    valuations = np.random.gamma(20.72054, 1/17.49951, txn_count)
    gas_prices = [self.basefee.value + (self.oracle.price(self.basefee.value) * v)
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

  def simulate(self, step_count, basefee_init, init_txns=8500, txns_per_turn=200):
    """ Run the simulation for n steps """

    # initialize variables
    block_data = pd.DataFrame()
    mempool_data = pd.DataFrame()
    mempools = []
    mempools_bf = []
    txn_counts = []

    self.basefee.value = basefee_init 
    basefees = [self.basefee.value]

    self.oracle = Oracle()
    self.update_mempool(init_txns)

    #iterate over n blocks
    for i in range(step_count):
      #fill blocks from mempools
      new_block, new_block_size = self.fill_block(i)
      self.blocks += [new_block]
      self.oracle.update(new_block)

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

class MultiSimulator(Simulator):

  """ Multidimensional EIP-1559 simulator. """

  def __init__(self, basefee, ratio, basefee_behavior="INDEPENDENT"):
    """
    [ratio]: example (0.7, 0.3) would split the [basefee] into 2 basefees with those
    relative values
    """
    super().__init__()
    self.basefee = [basefee.scaled_copy(ratio[0]), basefee.scaled_copy(ratio[1])]
    self.ratio = ratio
    self.basefee_behavior = basefee_behavior

  def total_bf(self):
    return self.basefee[0].value + self.basefee[1].value
    
  def update_mempool(self, txn_count, t=0):
    """
    Make [txn_number] new transactions and add them to the mempool
    """
    # the valuations and gas limits for the transactions. Following code from
    # 2021S
    valuations = np.random.gamma(20.72054, 1/17.49951, txn_count)
    bv = self.total_bf()
    gas_prices = [bv + (self.oracle.price(bv) * v)
                  for v in valuations]
    self.gas_price_batches += [gas_prices]

    if self.basefee_behavior == "CORRELATED":
      _gas_limits_single = (np.random.pareto(1.42150, txn_count)+1)*21000
      # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
      gas_limits_1 = [g*self.ratio[0] for g in _gas_limits_single]
      gas_limits_2 = [g*self.ratio[1] for g in _gas_limits_single]
      # this is completely correlated, so it really shouldn't affect basefee behavior
    else:
      assert (self.basefee_behavior == "INDEPENDENT")
      _gas_limits_1_single = (np.random.pareto(1.42150, txn_count)+1)*21000
      _gas_limits_2_single = (np.random.pareto(1.42150, txn_count)+1)*21000
      gas_limits_1 = [g*self.ratio[0] for g in _gas_limits_1_single]
      gas_limits_2 = [g*self.ratio[1] for g in _gas_limits_2_single]

    # store each updated mempool as a DataFrame

    self.mempool = pd.concat([self.mempool, pd.DataFrame({
        'gas price': gas_prices,
        'r1 limit': gas_limits_1,
        'r2 limit': gas_limits_2,
        'time': t,
        'amount paid': [x * (y+z) for x,y,z in
                        zip(gas_prices, gas_limits_1, gas_limits_2)]})],
                             ignore_index=True)
    
    # sort transactions in each mempool by gas price
    
    self.mempool = self.mempool.sort_values(by=['gas price'], ascending=False).reset_index(drop=True)

  def fill_block(self, time):
    """ create a block greedily from the mempool and return it"""
    block = []
    block_size = [0, 0]
    block_limit = [self.basefee[0].max_limit, self.basefee[1].max_limit]

    for i in range(len(self.mempool)):
      txn = self.mempool.iloc[i, :].tolist()
      if (txn[0] < self.total_bf() or
          block_size[0] + txn[1] > block_limit[0] or
          block_size[1] + txn[2] > block_limit[1]):
        break
        # strictly speaking we shouldn't break because maybe only one resource is full and
        # we can fill with the other resource; practically speaking this doesn't happen
      else:
        block.append(txn)
        block_size[0] += txn[1]
        block_size[1] += txn[2]

    block_wait_times = [time - txn[3] for txn in block]
    self.wait_times.append(block_wait_times)

    self.mempool = self.mempool.iloc[i+1: , :]
    return block, block_size

  def simulate(self, step_count, total_basefee_init, init_txns=8500, txns_per_turn=200):
    """ Run the simulation for n steps """

    # initialize empty dataframes
    block_data = pd.DataFrame()
    mempool_data = pd.DataFrame()
    mempools = []
    mempools_bf = []
    txn_counts = []

    self.oracle = Oracle()

    # sorted_block_mins = sorted([x - self.basefee.value if x >= self.basefee.value
    #                             else 0 for x in self.block_mins])

    self.basefee[0].value = total_basefee_init*self.ratio[0]
    self.basefee[1].value = total_basefee_init*self.ratio[1]
    basefees_1 = [self.basefee[0].value]
    basefees_2 = [self.basefee[1].value]
    basefees_tot = [self.total_bf()]

    #initialize mempools 
    self.update_mempool(init_txns)

    #iterate over n blocks
    for i in range(step_count):
      #fill blocks from mempools
      new_block, new_block_size = self.fill_block(i)
      self.blocks += [new_block]
      self.oracle.update(new_block)

      #update mempools

      self.basefee[0].update(new_block_size[0])
      self.basefee[1].update(new_block_size[1])
      basefees_1 += [self.basefee[0].value]
      basefees_2 += [self.basefee[1].value]
      basefees_tot += [self.total_bf()]

      mempools += [pd.DataFrame(self.mempool)]
      # this creates a copy; dataframes and lists are mutable
      mempools_bf += [self.mempool[self.mempool['gas price'] >= self.total_bf()]]
      # what does this do??

      # add 200 new txns before next iteration
      new_txns_count = random.randint(50, txns_per_turn*2 - 50)
      self.update_mempool(new_txns_count, i)

      txn_counts += [new_txns_count]

      # print("progress: ", i+1, end = '\r')
    return basefees_1, basefees_2, basefees_tot, self.blocks, mempools, mempools_bf, txn_counts, self.wait_times

  
# Plotting code

# sq_mempool_sizes_gl = [sum(x["gas limit"]) for x in sq_mempools_data]
# eip_mempool_sizes_bf_gl = [sum(x["gas limit"]) for x in eip_mempools_bf_data]

# plt.title("Mempool Sizes (Total Gas in Mempool)")
# plt.xlabel("Block Number")
# plt.ylabel("Total Gas")
# plt.plot(eip_mempool_sizes_bf_gl, label="eip-1559")
# plt.plot(sq_mempool_sizes_gl, label="status quo")
# plt.legend(loc="upper left")

# sq_mempool_sizes = [len(x) for x in sq_mempools_data]
# eip_mempool_sizes_bf = [len(x) for x in eip_mempools_bf_data]

# plt.title("Mempool Sizes (Total Txns in Mempool)")
# plt.xlabel("Block Number")
# plt.ylabel("# of Txns")
# plt.plot(eip_mempool_sizes_bf, label="eip-1559")
# plt.plot(sq_mempool_sizes, label="status quo")
# plt.legend(loc="upper left")

# eip_mempool_lrevs = [sum(i["amount paid"]) for i in eip_mempools_bf_data]
# sq_mempool_lrevs = [sum(i["amount paid"]) for i in sq_mempools_data]


# eip_ratios = []
# sq_ratios = []

# for i in range(len(sq_blocks_data) // 100):
#     eip_section = eip_wait_times[i*100:(i+1)*100]
#     sq_section = sq_wait_times[i*100:(i+1)*100]
    
#     eip_average = sum([sum(x) for x in eip_section]) / 100
#     sq_average = sum([sum(x) for x in sq_section]) / 100
    
#     X_sq = sum([sum([x for x in y if x <= sq_average ]) for y in sq_section])
#     X_eip = sum([sum([x for x in y if x <= eip_average]) for y in eip_section])
    
#     sq_waiting = len(sq_mempools_data[100*(i+1) - 1])
#     eip_waiting = len(eip_mempools_data[100*(i+1) - 1])
    
#     Y_sq = sum([sum([x for x in y if x > sq_average ]) for y in sq_section]) + sq_waiting
#     Y_eip = sum([sum([x for x in y if x > eip_average]) for y in eip_section]) + eip_waiting
    
#     eip_ratios.append(X_eip / Y_eip)
#     sq_ratios.append(X_sq / Y_sq)

# plt.title("Time Waiting Ratios")
# plt.xlabel("Block")
# plt.ylabel("Ratio")
# plt.plot([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], eip_ratios, label="eip-1559")
# plt.plot([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000], sq_ratios, label="status quo")
# plt.legend(loc="upper left")

# eip_avg_wait = [sum(x)/len(x) for x in eip_wait_times]
# sq_avg_wait = [sum(x)/len(x) for x in sq_wait_times]

# eip_rolling_avg = [sum(eip_avg_wait[i*10 : (i+1)*10]) / 10 for i in range(len(eip_avg_wait) // 10)]
# sq_rolling_avg = [sum(sq_avg_wait[i*10 : (i+1)*10]) / 10 for i in range(len(sq_avg_wait) // 10)]

# wait_ratios = [y // x for x, y in zip(eip_rolling_avg, sq_rolling_avg)]

# plt.title("Average Wait Times")
# plt.xlabel("Block")
# plt.ylabel("Wait Times")
# plt.plot([i*10 for i in range(100)], eip_rolling_avg, label="eip-1559")
# plt.plot([i*10 for i in range(100)], sq_rolling_avg, label="status quo")
# # plt.plot([i*10 for i in range(100)], wait_ratios, label="status quo / eip")
# plt.legend(loc="upper left")
