import numpy as np
import h5py
import math
import matplotlib.pyplot as plt
from scipy import stats
import random

# parameters for generating transaction model
lowerLimitCallData = 0
upperLimitCallData = 1000
lowerLimitGas=21000
upperLimitGas = 30000
aCallData=0.1581326153189052
betaCallData=0.0003219091599014724
proportionGasLowerLimit=0.1833810888252149
proportionCallDataLowerLimit=0
aGas=0.7419320005030383
betaGas=3.945088386120236e-06

# simulation parameters
maxCallData = 10000
maxGasData = 60000
gasLimit = 300000
operations_per_time_step = 50

# initial global variables
blockNumber = 0
baseFee = 1000
wait_times = []

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

class block():
    def __init__(self,transactions,time,prevBaseFee=None):
        self.transactions = transaction # store transactions as an array
        self.time = time
        # self.basefee = get_basefee(prevBaseFee,)

def get_basefee(b, g):
    return b * (1 + (1 / 8) * ((g - 15000000) / 15000000))

def create_transaction(time):
    # model call data and gas
    TxCallDataGenerated = float(stats.gamma.rvs(aCallData, scale=1 / betaCallData, size=1))
    ran = random.uniform(0, 1)
    if ran < proportionGasLowerLimit:
        TxGasGenerated = lowerLimitGas
    else:
        TxGasGenerated = float(stats.gamma.rvs(aGas, scale=1 / betaGas, size=1))

    call_data = resource("call_data",TxCallDataGenerated,upperLimitCallData, 22000)
    evm = resource("call_data",TxGasGenerated,upperLimitGas, 22000)
    resources = {"call_data":call_data,"evm":evm}
    return transaction(resources,time)

def populate_mempool(mempool,mempool_max_count,cur_time):
    newTransactionCount = mempool_max_count - len(mempool)
    for i in range(newTransactionCount):
        mempool.append(create_transaction(cur_time))

def create_block(mempool,time,gas_limit=None,method = None):
    # default block creation is random
    if method is None:
        method = "random"

    # initialize transaction list
    txs = []

    if method == "random":
        count = 0
        curCallData = 0
        curGasData = 0
        while(count<3):
            index = random.randint(0,len(mempool)-1)
            temp_transaction = mempool[index]
            if (maxCallData-(curCallData+temp_transaction.resources["call_data"].gas)>0 and maxGasData - (curGasData+temp_transaction.resources["evm"].gas)>0):
                curCallData += temp_transaction.resources["call_data"].gas
                curGasData += temp_transaction.resources["evm"].gas
                count = 0
                txs.append(temp_transaction)
                wait_times.append(time - temp_transaction.time)
                mempool.remove(temp_transaction)
            else:
                count += 1
        return block(txs,time)

    elif method == "greedy":
        # implement greedy algorithm
        print("This is greedy")
    elif method == "dp":
        # implement slightly optimized solver for knapsack problem
        print("This is dynamic")
    else:
        raise ValueError("Unknown solver block builder method")

class simultator():
    def __init__(self,mempool_size):
        self.t = 0 # epoch time
        # Initialize mempool
        self.mempool = []
        self.mempool_size = mempool_size
        populate_mempool(self.mempool,mempool_size,self.t)
        self.blocks = []

    def evolve(self):
        self.t += 1
        for i in range(operations_per_time_step):
            self.blocks.append(create_block(self.mempool,self.t))
        populate_mempool(self.mempool,self.mempool_size,self.t)

if __name__ == "__main__":
    sim = simultator(2000)
    for i in range(20):
        sim.evolve()
    plt.plot(wait_times)
    plt.show()