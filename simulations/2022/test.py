import os

from scipy import stats
import random
from simulations.simulator import Basefee, Simulator, Demand, Resource

if __name__=="__main__":
    basefee = Basefee(10000, 15000, 30000)
    b = basefee.scaled_copy(0.5)
    resource_in = ["call_data", "evm"]
    resources = [Resource("call_data","gamma",10,10),Resource("evm","gamma",10,10)]
    ratio = [0.5, 0.5]

    sim = Simulator(basefee, resources, ratio)
    demand = Demand(1000, 100, 51, 1000,resources=resources)
    # demand = Demand(1000, 100, 51, 1000)
    sim.simulate(demand)

    # lenGenerated = 10
    # TxGasGenerated = []
    # TxCallDataGenerated = []
    # for i in range(lenGenerated):
    #     TxCallDataGenerated.append(float(stats.gamma.rvs(aCallData, scale=1 / betaCallData,
    #                                                      size=1)))  # must change to break into if statement below to generate diff calldata distr when gas=21k
    #     ran = random.uniform(0, 1)
    #     # ran2=random.uniform(0,1) #dont want to make mixture model for call data with 0s
    #     if ran < proportionGasLowerLimit:
    #         TxGasGenerated.append(lowerLimitGas)
    #     else:
    #         TxGasGenerated.append(float(stats.gamma.rvs(aGas, scale=1 / betaGas, size=1)))
    #     # if ran2<proportionCallDataLowerLimit:
    #     #    TxCallDataGenerated.append(lowerLimitCallData)
    #     # else:
    #     # TxGasGenerated.append(float(stats.gamma.rvs(aGas, scale=1/betaGas,size=1)))