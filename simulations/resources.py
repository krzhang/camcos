from typing import List,Optional
from abc import ABC,abstractmethod
import numpy as np
import random
from scipy import stats
from constants import MAX_LIMIT, INFTY
from settings import DATA_PATH
import pandas as pd
from bisect import bisect
from ast import literal_eval

class Basefee():

  def __init__(self, d, target_limit, max_limit, value=0.0):
    """
    :param target_limit: target gas limit (e.g. 1.5M gas)
    :param max_limit: max limit (e.g. 3M gas)
    :param d: the scaling factor in the basefee update (see update())
    :param value: the value of the basefee at any particular time
    """
    self.target_limit = target_limit
    self.max_limit = max_limit
    self.d = d
    self.value = value

  def scaled_copy(self, ratio):
    """ gives a scaled copy of the same basefee objects; think of it as a decominator change """
    # note that value doesn't change; if we split pricing for a half steel half bronze item
    # into pricing for steel vs bronze, the volumes are halved but the values stay the same by
    # default
    return Basefee(self.d, self.target_limit * ratio, self.max_limit * ratio, self.value)

  def update(self, gas):
    """ return updated basefee given [b] original basefee and [g] gas used"""
    if self.target_limit == 0:
      pass
    else:
      self.value = self.value * (1 + self.d * ((gas - self.target_limit) / self.target_limit))

  def value_setter(self,value):
    """Setter for basefee"""
    self.value = value


class ResourcePackage(ABC):
  """
  Super class of multiple resources. Generate function should return a dictionary of {resource:[values]}. This can be passed in to Demand and Simulator class
  """
  def __init__(self,resource_names: List,resource_behavior,basefee,split: bool,ratio=None):
    """
    Default Constructor
    :param resource_names: Take in a list of resources. Converts everything to string so we can also pass in class BasicResource
    :param resource_behavior: INDEPENDENT, CORRELATED, INDIVIDUAL or JOINT
    :param basefee: Dictionary of basefee objects. {resource_name: Basefee}
    :param split: True for X+Y=Z method. False for X+Y method
    """
    self.resource_names = [str(x) for x in resource_names]
    self.dimension = len(self.resource_names)
    self.resource_behavior = resource_behavior
    self.basefee = basefee
    self.split = split
    if split is True:
      assert ratio is not None
    self.ratio = ratio

  @abstractmethod
  def generate(self):
    """
    Child class must override this function and return a dictionary of {resource:value}
    """
    pass

class IndependentResources(ResourcePackage):
  """
  Child class of ResourcePackage. Resources are generated by generating one number and splitting it n-ways randomly
  """
  def __init__(self,resource_names: List[str],ratio: List[float],basefee:Basefee,alpha=1.42150,beta=21000):
    """
    Default Constructor
    :param resource_names: List of resource names
    :param ratio: An array of ratios. Eg: (0.7, 0.3) would split the resource into 2 basefees with those relative
    values. But it doesn't matter much here since the ratios will be randomized to produce uncorrelated resources
    :param basefee: Basefee object. Constructor will handle splitting before passing into ResourcePackage
    :param alpha: Alpha value for pareto distribution
    :param beta: Beta value for pareto distribution
    """

    assert(sum(ratio)==1)
    resource_names = [str(x) for x in resource_names]
    self.basefee_init = basefee.value
    self.ratio = {resource_names[i]: ratio[i] for i in range(len(resource_names))}
    self.basefee = {}
    for r in resource_names:
      self.basefee[r] = basefee.scaled_copy(self.ratio[r])
      # self.basefee[r].value_setter(self.basefee_init*self.ratio[r])

    super().__init__(resource_names, "INDEPENDENT",self.basefee, True,self.ratio)
    # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
    self.alpha = alpha
    self.beta = beta

  def generate(self):
    # Generate 1 number
    _limits_sample = (np.random.pareto(self.alpha, 1) + 1) * self.beta
    _limits_sample = min(_limits_sample[0], MAX_LIMIT)

    # Twiddle ratio code
    new_ratios = {x: random.uniform(0.0, self.ratio[x]) for x in self.ratio}
    normalization = sum(new_ratios[x] for x in new_ratios)
    newer_ratios = {x: new_ratios[x] / normalization for x in self.ratio}

    limits = {r:min(_limits_sample * newer_ratios[r], self.basefee[r].max_limit) for r in self.resource_names}
    return limits

class CorrelatedResources(ResourcePackage):
  """
  Child class of ResourcePackage. Resources are generated by generating one number and splitting it with the given ratio
  """
  def __init__(self,resource_names: List[str],ratio: List[int],basefee:Basefee,alpha=1.42150,beta=21000):
    """
    Default Constructor
    :param resource_names: List of resource names
    :param ratio: An array of ratios. Eg: (0.7, 0.3) would split the resource into 2 basefees with those relative
    values.
    :param basefee: Basefee object. Constructor will handle splitting before passing into ResourcePackage
    :param alpha: Alpha value for pareto distribution
    :param beta: Beta value for pareto distribution
    """
    assert (sum(ratio) == 1)
    resource_names = [str(x) for x in resource_names]
    self.basefee_init = basefee.value
    self.ratio = {resource_names[i]: ratio[i] for i in range(len(resource_names))}
    self.basefee = {}
    for r in resource_names:
      self.basefee[r] = basefee.scaled_copy(self.ratio[r])
      # self.basefee[r].value_setter(self.basefee_init * self.ratio[r])

    super().__init__(resource_names, "CORRELATED", self.basefee, True, self.ratio)
    # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
    self.alpha = alpha
    self.beta = beta

  def generate(self):
    _limits_sample = (np.random.pareto(self.alpha, 1) + 1) * self.beta
    _limits_sample = min(_limits_sample[0], MAX_LIMIT)

    limits = {r:min(_limits_sample * self.ratio[r], self.basefee[r].max_limit) for r in self.resource_names}
    return limits

# This is for the X+Y method of doing resources instead of Z=X+Y
class BasicResource(ABC):
  """
  Class for creating a singular resource profile. Super class for individual resources that generate their own values.
  Adam's old code from TxSimulations.ipynb
  """
  def __init__(self, name,basefee: Basefee):
    """
    Default Constructor
    :param name: Name of the resource
    :param basefee: Basefee object
    """
    self.name = name
    self.basefee = basefee

  @abstractmethod
  def generate(self):
    """
    Child class must override generate function
    """
    pass

  def __str__(self):
    """
    Ensures that an array of BasicResource can be passed into ResourcePackage by converting it into string when
    str() is called
    :return: Name of resource
    """
    return self.name

class BasicCallData(BasicResource):
  def __init__(self,basefee: Basefee,alpha = 0.1581326153189052,beta = 0.0003219091599014724,proportionLimit=None,lowerLimit = None):
    """
    Child class from BasicResource
    :param basefee: Basefee object to initialize BasicResource
    :param alpha, beta: Found values from TxSimulations.ipynb
    :param proportionLimit: If given, when random number generator is less than this number, lowerLimit will be generated
    :param lowerLimit: lowest default value
    :param basefee
    """
    super().__init__("call_data",basefee)
    self.alpha = alpha
    self.beta = beta
    self.proportionLimit = proportionLimit
    self.lowerLimit = lowerLimit

  def generate(self):
    if self.proportionLimit is None:
      if self.basefee.max_limit is None:
        return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
      else:
        return min(float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1)),self.basefee.max_limit)
    else:
      ran = random.uniform(0, 1)
      # ran2=random.uniform(0,1) #dont want to make mixture model for call data with 0s
      if ran < self.proportionLimit:
        return self.lowerLimit
      else:
        if self.basefee.max_limit is None:
          return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
        else:
          return min(float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1)), self.basefee.max_limit)

class BasicGas(BasicResource):
  def __init__(self,basefee:Basefee,alpha = 0.7419320005030383,beta = 3.945088386120236e-06,proportionLimit=0.1833810888252149,lowerLimit = 21000):
    super().__init__("gas",basefee)
    self.alpha = alpha
    self.beta = beta
    self.proportionLimit = proportionLimit
    self.lowerLimit = lowerLimit

  def generate(self):
    if self.proportionLimit is None:
      if self.basefee.max_limit is not None:
        return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
      else:
        return min(float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1)), self.basefee.max_limit)
    else:
      ran = random.uniform(0, 1)
      # ran2=random.uniform(0,1) #dont want to make mixture model for call data with 0s
      if ran < self.proportionLimit:
        return self.lowerLimit
      else:
        if self.basefee.max_limit is None:
          return float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1))
        else:
          return min(float(stats.gamma.rvs(self.alpha, scale=1 / self.beta, size=1)), self.basefee.max_limit)

class IndividualResources(ResourcePackage):
  """
  Takes in an array of BasicResource so that we can generate values with X+Y method
  """
  def __init__(self,resource_names: List[BasicResource]):
    self.resource_package = resource_names
    basefee_package = {str(x):x.basefee for x in resource_names}
    super().__init__(resource_names,"INDIVIDUAL",basefee_package,False)

  def generate(self):
    """
    Calls generate function for each BasicResource
    :return:
    """
    limits = {str(r):r.generate() for r in self.resource_package}
    return limits

class JointResources(ResourcePackage):
  """
  Adam's code. Reads in csv from /data/
  """

  def __init__(self,resource_names: List[str],bf_standard:Basefee, call_data_standard:Basefee,filename="specialGeneration.csv"):
    # self.resource_package = resource_names
    self.resource_package = ["gas","call_data"]

    basefee_package = {"gas":bf_standard, "call_data":call_data_standard}
    ###
    super().__init__(self.resource_package,"JOINT",basefee_package,False)
    self.filename = filename

  def generate(self):
    df = pd.read_csv(str(DATA_PATH)+"/"+self.filename)
    rand = random.random()

    index = bisect(df["Additive Ratio"],rand)
    generation_type = df["Type"][index]
    gas = df["Gas Value"][index]
    call_data = df["Calldata Length"][index]

    if generation_type == "CDDistribution":
      gas = float(stats.gamma.rvs(df["Alpha Gamma Parameter"][index], scale=1 /df["Beta Gamma Parameter"][index] , size=1))
    elif generation_type == "GasDistribution":
      call_data = float(stats.gamma.rvs(df["Alpha Gamma Parameter"][index], scale=1 /df["Beta Gamma Parameter"][index] , size=1))
    elif generation_type == "Point":
      pass
    elif generation_type == "Remaining":
      call_data, gas = np.random.multivariate_normal(literal_eval(df["Mu Lognormal Parameter"][index]),
                                                     literal_eval(df["Cov Lognormal Parameter"][index]), 1).T
      call_data = call_data[0]
      gas = gas[0]
    else:
      raise ValueError("Distribution type not found")
    return {"gas":gas,"call_data":int(call_data)}
