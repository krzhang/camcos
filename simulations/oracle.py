import pandas as pd
# from collections import deque

DEFAULT_ORACLE_INDEX = 60 # current geth oracle looks at the 60th smallest 

def load_data(filename, basefee_init, depth=100):
  """
  read in data from a CSV to create the right context for simulations. Return as DataFrame.
  This entire function is hackish and is meant to get some initial conditions working.

  [depth]: how many transactions we look at before initializing data

  returns
  [min_tips]: an array of [depth] minimal tips (lower bounded at 0) above basefee that it took to
    be included.
  [basefees]: an array of [depth] historical basefees (for now they are just all copies of a single
    initial basefee, since our data doesn't have basefee)
  """
  ### Temporary solution, block data is not read properly in python file path
  directory = "/Users/teohyikhaw/PycharmProjects/camcos_f2022/simulations/"
  data = pd.read_csv(directory+filename)
  df = data[['gasLimit', 'minGasPrice']].values # eventually we might find other things worthwhile

  basefees = []
  min_tips = []
  for d in df:
    if len(min_tips) == depth:
      break
    if d[1] == 'None':
      continue
    price = int(d[1]) / 10**9
    min_tip = (price - basefee_init if price >= basefee_init else 0)
    min_tips.append(min_tip)
  assert (len(min_tips) == depth)
  basefees = [basefee_init]*depth
  return min_tips, basefees

class Oracle():
  """ Handler for all oracle (e.g. Geth) related logic. Handles muilti-dimensional EIP-1559. """

  def __init__(self, resources, ratio, basefee_init, filename="block_data.csv", gas_prices = None):
    """ 
    read in data to initialize oracle. The main object is [block_mins], a list of block minimums
    for future oracle updates.

    [resources] - something like ("computation", "storage")
    [ratio] - something like (0.7, 0.3)). 
    For a single dimension the above should be ("gas",) and (1.0,).

    [basefee_init] - initial basefee

    the main exposed item is rec_tips, which is a dictionary from resources to the recommended tip

    [gas_price] - array of gas prices of each individual resource, if set to None, will assume equally priced
    """
    self.resources = resources
    self.ratio = ratio
    # the main oracle object, storing the block minimums (min price needed to get in block)
    # (keep sorted) TODO: use a heap
    self.oracle_index = 60  # the oracle price is the 60th price in the sorted block mins
    min_tips, _ = load_data(filename, basefee_init)
    assert len(min_tips) > self.oracle_index

    # this is a hack: since we aren't given the separate resource prices from the CSV, we need
    # to fake them. As a first iteration, we can assume that the 2 types of goods are priced
    # the same
    # we also have to fake historical basefees. Again, we assume historically the basefees are
    # just what's given
    self.gas_prices = gas_prices

    self.min_tips = {}
    for r in resources:
      self.min_tips[r] = min_tips.copy()
    self.rec_tips = {}  # this is where the oracle price is
    self.set_rec_tips()

  def set_rec_tips(self):
    for r in self.resources:
      sorted_min_tips = sorted(self.min_tips[r])
      self.rec_tips[r] = sorted_min_tips[self.oracle_index - 1]

  def update(self, block_min_tip):
    """
    given a block is finished, update the oracle.
    [block_min_tip]:
    a dictionary indexed by resource of the min tips required to be 
    included in the block
    """
    # old:
    # recent_gp = block[-1][1]
    # self.block_mins.popleft()
    # self.block_mins.append(recent_gp)
    for r in self.resources:
      self.min_tips[r] = self.min_tips[r][1:] + [block_min_tip[r]]
