import numpy as np
import pandas as pd
import random
from simulations import oracle

INFTY = 3000000
MAX_LIMIT = 8000000

class Demand():
  """ class for creating a demand profile """

  def __init__(self, init_txns, txns_per_turn, step_count, basefee_init):
    self.valuations = []
    self.limits = []
    for i in range(step_count+1):
      # we add 1 since there's just also transactions to begin with
      if i == 0:
        txn_count = init_txns
      else:
        txn_count = random.randint(50, txns_per_turn * 2 - 50)

      # the mean for gamma(k, \theta) is k\theta, so the mean is a bit above 1.
      # note we use the initial value as a proxy for a "fair" basefee; we don't want people to
      # arbitrarily follow higher basefee, then it will spiral out of control
      # in particular, these people don't use a price oracle!

      self.valuations.append(np.random.gamma(20.72054, 1/17.49951, txn_count))

      # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
      _limits_sample = (np.random.pareto(1.42150, txn_count)+1)*21000
      _limits_sample = [min(l, MAX_LIMIT) for l in _limits_sample]
      self.limits.append(_limits_sample)

class Basefee():

  def __init__(self, d, target_limit, max_limit, value=0.0):
    self.target_limit = target_limit
    self.max_limit = max_limit
    self.d = d
    self.value = value

  def scaled_copy(self, ratio):
    """ gives a scaled copy of the same basefee objects; think of it as a decominator change """
    # note that value doesn't change; if we split pricing for a half steel half bronze item
    # into pricing for steel vs bronze, the volumes are halved but the values stay the same by
    # default
    return Basefee(self.d, self.target_limit*ratio, self.max_limit*ratio, self.value)

  def update(self, gas):
    """ return updated basefee given [b] original basefee and [g] gas used"""
    self.value = self.value*(1+self.d*((gas-self.target_limit)/self.target_limit))


class Simulator():

  """ Multidimensional EIP-1559 simulator. """

  def __init__(self, basefee, resources, ratio, resource_behavior="INDEPENDENT",knapsack_solver=None):
    """
    [ratio]: example (0.7, 0.3) would split the [basefee] into 2 basefees with those
    relative values
    """
    assert len(ratio) == len(resources)
    self.resources = resources
    self.dimension = len(resources) # number of resources
    self.resource_behavior = resource_behavior
    self.knapsack_solver=knapsack_solver

    # everything else we use is basically a dictionary indexed by the resource names
    self.ratio = {resources[i]:ratio[i] for i in range(self.dimension)}
    self.basefee = {}
    self.basefee_init = basefee.value
    for r in self.resources:
      self.basefee[r] = basefee.scaled_copy(self.ratio[r])

    self.mempool = pd.DataFrame([])
  # def total_bf(self):
  #   return self.basefee[0].value + self.basefee[1].value

  def _twiddle_ratio(self):
    """ given a ratio, twiddle the ratios a bit"""
    ratio = self.ratio
    new_ratios = {x:random.uniform(0.0, ratio[x]) for x in ratio}
    normalization = sum(new_ratios[x] for x in new_ratios)
    newer_ratios = {x:new_ratios[x]/normalization for x in ratio}
    return newer_ratios
  
  def update_mempool(self, demand, t):
    """
    Make [txn_number] new transactions and add them to the mempool
    """
    # the valuations and gas limits for the transactions. Following code from
    # 2021S
    prices = {}

    _valuations = demand.valuations[t]
    txn_count = len(_valuations)
    
    for r in self.resources:
      prices[r] = [self.basefee_init * v for v in _valuations]

    limits = {}
    _limits_sample = demand.limits[t]
    
    if self.resource_behavior == "CORRELATED":
      for r in self.resources:
        limits[r] = [min(g*self.ratio[r], self.basefee[r].max_limit)
                     for g in _limits_sample]
      # this is completely correlated, so it really shouldn't affect basefee behavior
    else:
      assert (self.resource_behavior == "INDEPENDENT")
      new_ratios = self._twiddle_ratio()
      for r in self.resources:
        limits[r] = [min(g*new_ratios[r], self.basefee[r].max_limit)
                     for g in _limits_sample]

    # store each updated mempool as a DataFrame. Here, each *row* will be a transaction.
    # we will start with 2*[dimension] columns corresponding to prices and limits, then 2
    # more columns for auxiliary data

    total_values = [sum([prices[r][i] * limits[r][i] for r in self.resources]) for
                    i in range(txn_count)]

    data = []
    for r in self.resources:
      data.append((r + " price", prices[r]))
      data.append((r + " limit", limits[r]))
    data.append(("time", t)) # I guess this one just folds out to all of them?
    data.append(("total_value", total_values))
    data.append(("profit", 0))
    txns = pd.DataFrame(dict(data))

    self.mempool = pd.concat([self.mempool, txns])

  def _compute_profit(self, tx):
    """ 
    Given a txn (DataFrame), compute the profit (given current basefees). This is the difference
    between its [total_value] and the burned basefee

    """
    txn = tx.to_dict()
    burn = sum([txn[r + " limit"] * self.basefee[r].value for r in self.resources])
    return tx["total_value"] - burn
    
  def fill_block(self, time, method=None):
    if method is None:
      method = "greedy"

    """ create a block greedily from the mempool and return it"""
    block = []
    block_size = {r:0 for r in self.resources}
    block_max = {r:self.basefee[r].max_limit for r in self.resources}
    block_min_tip = {r:INFTY for r in self.resources}
    # the minimal tip required to be placed in this block

    # we now do a greedy algorithm to fill the block.

    # 1. we sort transactions in each mempool by total value in descending order


    self.mempool['profit'] = self.mempool.apply(self._compute_profit, axis = 1)
    if method == "greedy:":
      self.mempool = self.mempool.sort_values(by=['profit'],
                                            ascending=False).reset_index(drop=True)
    # randomly choose blocks by not sorting them
    elif method == "random":
      self.mempool = self.mempool.reset_index(drop=True)

    # 2. we keep going until we get stuck (basefee too high, or breaks resource limit)
    #    Since we might have multiple resources and we don't want to overcomplicate things,
    #    our hack is just to just have a buffer of lookaheads ([patience], which decreases whenever
    #    we get stuck) and stop when we get stuck.
    patience = 10
    included_indices = []
    for i in range(len(self.mempool)):
      tx = self.mempool.iloc[i, :]
      txn = tx.to_dict()
      # this should give something like {"time":blah, "total_value":blah...
      # TODO: should allow negative money if it's worth a lot of money in total
      if (any(txn[r + " limit"] + block_size[r] > block_max[r] for r in self.resources) or
          txn["profit"] < 0):
        if patience == 0:
          break
        else:
          patience -= 1
      else:
        block.append(txn)
        included_indices.append(i)
        # faster version of self.mempool = self.mempool.iloc[i+1:, :]
        for r in self.resources:
          block_size[r] += txn[r + " limit"]
          if txn[r + " price"] - self.basefee[r].value < block_min_tip[r]:
            block_min_tip[r] = txn[r + " price"] - self.basefee[r].value
            
    self.mempool.drop(included_indices, inplace=True)
    # block_wait_times = [time - txn["time"] for txn in block]
    # self.wait_times.append(block_wait_times)

    return block, block_size, block_min_tip

  def simulate(self, demand):
    """ Run the simulation for n steps """

    # initialize empty dataframes
    blocks = []
    mempools = []
    new_txn_counts = []
    used_txn_counts = []
    self.oracle = oracle.Oracle(self.resources, self.ratio, self.basefee_init)

    basefees = {r:[self.basefee[r].value] for r in self.resources}
    limit_used = {r:[] for r in self.resources}
    min_tips = {r:[] for r in self.resources}
    #initialize mempools 
    self.update_mempool(demand, 0) # the 0-th slot for demand is initial transactions

    step_count = len(demand.valuations) - 1
    
    #iterate over n blocks
    for i in range(step_count):
      #fill blocks from mempools
      new_block, new_block_size, new_block_min_tips = self.fill_block(i,method=self.knapsack_solver)
      blocks += [new_block]
      self.oracle.update(new_block_min_tips)

      #update mempools

      for r in self.resources:
        self.basefee[r].update(new_block_size[r])
        basefees[r] += [self.basefee[r].value]
        limit_used[r].append(new_block_size[r])
        min_tips[r].append(new_block_min_tips[r])

      # # Commented: save mempools (expensive!)
      # # if we do use them, this creates a copy; dataframes and lists are mutable
      # mempools += [pd.DataFrame(self.mempool)]
      
      # mempools_bf += [self.mempool[self.mempool['gas price'] >= self.total_bf()]]
      # what does this do??

      # new txns before next iteration
      # we want supply to match demand;
      # right now target gas is 15000000, each transaction is on average 2.42*21000 = 52000 gas,
      # so we should shoot for 300 transactions per turn

      used_txn_counts.append(len(new_block))
      
      self.update_mempool(demand, i+1)# we shift by 1 because of how demand is indexed
      new_txns_count = len(demand.valuations[i+1])
      
      new_txn_counts.append(new_txns_count)

    block_data = {"blocks":blocks,
                  "limit_used":limit_used,
                  "min_tips":min_tips}
    mempool_data = {"new_txn_counts":new_txn_counts,
#                    "mempools":mempools,
                    "used_txn_counts":used_txn_counts}
    return basefees, block_data, mempool_data

  
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