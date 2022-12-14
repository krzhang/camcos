import os
import sys; sys.path.insert(0, '..')
import h5py
import uuid
from simulator import Simulator,Demand,run_simulations
# from oracle import Oracle
from resources import BasicResource, ResourcePackage, IndependentResources, CorrelatedResources, IndividualResources
from resources import BasicCallData, BasicGas, JointResources, Basefee
import socket

if __name__ == "__main__":
    bf_standard_value = 38.100002694
    bf_standard = Basefee(1.0 / 8, 15000000, 30000000, bf_standard_value)
    resource_package = IndependentResources(["gas", ""], [1.0, 0.0], bf_standard)
    demand = Demand(2000, 0, 400, resource_package)
    sim = Simulator(demand)
    basefees_data, block_data, mempools_data, basefees_stats = sim.simulate(400)

    import matplotlib.pyplot as plt
    plt.rcParams["figure.figsize"] = (15, 10)
    plt.title("Basefee over Time")
    plt.xlabel("Block Number")
    plt.ylabel("Basefee (in Gwei)")
    plt.plot(basefees_data["gas"])
    plt.show()