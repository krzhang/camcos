import numpy as np
import h5py
import math
from scipy import stats
import random

class resource():
    def __init__(self,name,gas,gas_limit,amount_paid):
        self.name = name
        self.gas = gas
        self.gas_limit = gas_limit
        self.amount_paid = amount_paid

class transaction():
    def __init__(self, resources, time):
        self.resources = resources # take in dictionary of class of type resource
        self.time = time

def create_transaction(time):
    # lenGenerated = 10
    # TxGasGenerated = []
    # TxCallDataGenerated = []
    # for i in range(lenGenerated):
    #     TxCallDataGenerated.append(float(stats.gamma.rvs(aCallData, scale=1 / betaCallData, size=1)))
    #     ran = random.uniform(0, 1)
    #     ran2 = random.uniform(0, 1)
    #     if ran < proportionGasLowerLimit:
    #         TxGasGenerated.append(lowerLimitGas)
    #     else:
    #         TxGasGenerated.append(float(stats.gamma.rvs(aGas, scale=1 / betaGas, size=1)))
    #     if ran < proportionCallDataLowerLimit:
    #         TxCallDataGenerated.append(lowerLimitCallData)
    #     else:
    #         TxGasGenerated.append(float(stats.gamma.rvs(aGas, scale=1 / betaGas, size=1)))

    call_data = resource("call_data",21000,30000, 22000)
    evm = resource("call_data",21000,30000, 22000)
    resources = {"call_data":call_data,"evm":evm}
    return transaction(resources,time)

def populate_mempool(mempool,mempool_max_count,cur_time):
    newTransactionCount = mempool_max_count - len(mempool)
    for i in range(newTransactionCount):
        mempool.append(create_transaction(cur_time))

def create_block(mempool,gas_limit):
    # implement solver for knapsack problem
    print()

class simultator():
    def __init__(self,mempool_size):
        self.t = 0 # epoch time
        # Initialize mempool
        self.mempool = []
        self.mempool_size = mempool_size
        populate_mempool(self.mempool,mempool_size,self.t)

    def evolve(self):
        self.t+=1
        populate_mempool(self.mempool,self.mempool_size,self.t)
        print()



if __name__ == "__main__":
    sim = simultator()
