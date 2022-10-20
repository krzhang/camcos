import numpy as np
import pandas as pd
import random
from simulations import oracle
import os
import h5py
import matplotlib.pyplot as plt
import uuid
from scipy import stats

INFTY = 3000000
MAX_LIMIT = 8000000

# This is for the X+Y method of doing resources instead of Z=X+Y
class Resource():
  def __init__(self,name,distribution,alpha,beta,proportionLimit=None,lowerLimit = None):
    self.name = name
    self.distribution = distribution
    self.alpha = alpha
    self.beta = beta
    self.proportionLimit = proportionLimit
    self.lowerLimit = lowerLimit
  def generate(self):
    if self.distribution == "gamma":
      if self.proportionLimit is None:
        return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
      else:
        ran = random.uniform(0, 1)
        # ran2=random.uniform(0,1) #dont want to make mixture model for call data with 0s
        if ran < self.proportionLimit:
          return self.lowerLimit
        else:
          return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
  def __str__(self):
    return self.name

class Demand():
  """ class for creating a demand profile """

  def __init__(self, init_txns, txns_per_turn, step_count, basefee_init, resources = None):
    self.valuations = []
    self.limits = []
    self.step_count = step_count
    self.resources = resources

    # Check if resources is a list of class resources
    if resources is not None:
      assert isinstance(resources,list)
      for i in resources:
        assert (isinstance(i, Resource))

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

      # Previous code
      if resources is None:
        # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
        _limits_sample = (np.random.pareto(1.42150, txn_count)+1)*21000
        _limits_sample = [min(l, MAX_LIMIT) for l in _limits_sample]
        self.limits.append(_limits_sample)
      else:
        self.limits.append([tuple(resource.generate() for resource in resources) for x in range(txn_count)])

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

    if knapsack_solver is None:
      self.knapsack_solver = "greedy"
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

    # checks if resources are manually placed in
    if demand.resources is not None:
      self.resource_behavior = "SEPARATED"

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
    elif self.resource_behavior == "INDEPENDENT":
      new_ratios = self._twiddle_ratio()
      for r in self.resources:
        limits[r] = [min(g*new_ratios[r], self.basefee[r].max_limit)
                     for g in _limits_sample]
    else:
      # assert self.resource_behavior == "SEPARATED"
      # Copy over generated values from demand
      for r in range(len(self.resources)):
        limits[self.resources[r]] = [_limits_sample[i][r] for i in range(len(_limits_sample))]

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
    if method == "greedy":
      self.mempool = self.mempool.sort_values(by=['profit'],
                                            ascending=False).reset_index(drop=True)
    # randomly choose blocks by not sorting them
    elif method == "random":
      self.mempool = self.mempool.sample(frac=1).reset_index(drop=True)

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

def generate_simulation(simulator, demand, num_iterations, filetype=None, filepath=None):
  # Input checking and processing
  if filetype is None:
    filetype = "hdf5"
  assert filetype == "hdf5" or filetype == "csv" or filetype == "hdf5+csv"
  if filepath is None:
    filepath = os.getcwd() + "/generated_data/"
    if not os.path.exists(filepath):
      os.mkdir(filepath)

  # Create file path if does not exist
  if not os.path.exists(filepath+"/figures/"):
    os.mkdir(filepath+"/figures/")
  if not os.path.exists(filepath+"/data/"):
    os.mkdir(filepath+"/data/")

  created_files = []

  for i in range(num_iterations):
    basefees_data, block_data, mempools_data = simulator.simulate(demand)

    plt.rcParams["figure.figsize"] = (15, 10)
    plt.title("Basefee over Time")
    plt.xlabel("Block Number")
    plt.ylabel("Basefee (in Gwei)")
    plt.plot(basefees_data["gas"], label="gas")
    basefees_data_space = [x + 1 for x in basefees_data["space"]]
    plt.plot(basefees_data_space, label="space")
    plt.legend(loc="upper left")
    # plt.show()

    # Save hdf5 file
    uniqueid = str(uuid.uuid1()).rsplit("-")[0]
    filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-{uuid}".format(simulator.dimension,
                                                                               x=simulator.resource_behavior,
                                                                               y=simulator.knapsack_solver, uuid=uniqueid)

    plt.savefig(filepath+"/figures/" + filename + ".png")
    plt.cla()

    if filetype == "hdf5" or filetype == "hdf5+csv":
      f = h5py.File(filepath+"/data/" + filename + ".hdf5", "w")
      f.create_dataset("gas", data=basefees_data["gas"], compression="gzip")
      f.create_dataset("space", data=basefees_data_space, compression="gzip")
      f.close()
      print("Saving hdf5 as "+ filename+".hdf5")
      created_files.append(filename + ".hdf5")
    if filetype == "csv" or filetype == "hdf5+csv":
      df = pd.DataFrame({"gas": basefees_data["gas"], "space": basefees_data_space})
      df.to_csv(filepath + "/data/" +filename + ".csv", index=False)
      print("Saving csv as " + filename + ".csv")
      created_files.append(filename + ".csv")

  # Take average of all files
  gas_average = [0 for x in range(demand.step_count+1)]
  space_average = [0 for x in range(demand.step_count+1)]
  for filename in created_files:
    if filetype == "hdf5" or filetype == "hdf5+csv":
      f = h5py.File(filepath + "/data/" + filename, "r")
      gas_average = np.add(gas_average, list(f["gas"]))
      space_average = np.add(space_average, list(f["space"]))
    else:
      df = pd.read_csv(filepath+"/data/"+filename)
      gas_average = np.add(gas_average, df["gas"])
      space_average = np.add(space_average, df["space"])

  gas_average = [x / num_iterations for x in gas_average]
  space_average = [x / num_iterations for x in space_average]

  # Save data as hdf5
  filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-averaged".format(2, x=simulator.resource_behavior,
                                                                               y=simulator.knapsack_solver)
  if filetype == "hdf5" or filetype == "hdf5+csv":
    f = h5py.File(filepath +"/data/"+ filename + ".hdf5", "w")
    f.create_dataset("gas", data=gas_average, compression="gzip")
    f.create_dataset("space", data=space_average, compression="gzip")
    f.close()

  if filetype == "csv" or filetype == "hdf5+csv":
    # Save data as csv
    df = pd.DataFrame({"gas": gas_average, "space": space_average})
    df.to_csv(filepath +"/data/"+ filename + ".csv", index=False)

  plt.rcParams["figure.figsize"] = (15, 10)
  plt.title("Basefee over Time. {0:d} iterations".format(num_iterations))
  plt.xlabel("Block Number")
  plt.ylabel("Basefee (in Gwei)")
  plt.plot(gas_average, label="gas")
  plt.plot(space_average, label="space")
  plt.legend(loc="upper left")
  plt.savefig(filepath +"/figures/" + filename + ".png")
  plt.show()

  return gas_average, space_average
  
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
