from simulations.simulator import Basefee, Simulator, Demand
from simulations.oracle import Oracle
import matplotlib.pyplot as plt

if __name__=="__main__":
    # basefee = Basefee(10000,15000,30000)
    # b = basefee.scaled_copy(0.5)
    # resource_in = ["call_data","evm"]
    # ratio = [0.5,0.5]
    #
    #
    # sim = Simulator(basefee,resource_in,ratio)
    # demand = Demand(1000,100,51,1000)
    # sim.simulate(demand)

    bf_standard_value = 38.100002694
    bf_standard = Basefee(1.0 / 8, 15000000, 30000000, bf_standard_value)  # d, target gas, max gas
    # note our gas maxima are "real-life" amounts, but our actual gas per transaction is about 10x
    # bigger, for sake of simplicity

    demand = Demand(2000, 300, 400, bf_standard_value)

    mbf_sim = Simulator(bf_standard, ("gas", "space"), (0.7, 0.3), resource_behavior="CORRELATED")
    basefees_data, block_data, mempools_data = mbf_sim.simulate(demand)

    plt.rcParams["figure.figsize"] = (15, 10)
    plt.title("Basefee over Time")
    plt.xlabel("Block Number")
    plt.ylabel("Basefee (in Gwei)")
    plt.plot(basefees_data["gas"], label="gas")
    basefees_data_space = [x + 1 for x in basefees_data["space"]]
    plt.plot(basefees_data_space, label="space")
    plt.legend(loc="upper left")
    plt.show()
