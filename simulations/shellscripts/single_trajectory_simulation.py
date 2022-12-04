import os
import sys; sys.path.insert(0, '..')
import h5py
import uuid
from simulator import Simulator,Demand,run_simulations
# from oracle import Oracle
from resources import BasicResource, ResourcePackage, IndependentResources, CorrelatedResources, IndividualResources
from resources import BasicCallData, BasicGas, JointResources, Basefee
import matplotlib.pyplot as plt
import socket

def save_simulation(data, attributes, filename, filepath):
    f = h5py.File(filepath + filename + ".hdf5", "a")

    for i in attributes.keys():
        f.attrs[str(i)] = attributes[i]

    # this is a cheap and quick way, very hardcoded
    basefees_stats_save = f.create_group("basefees_stats")
    basefees_stats_save.create_dataset("basefees_variance",
                                       data=list(data["basefees_stats"]["basefees_variance"].values()),
                                       compression="gzip")
    basefees_stats_save.create_dataset("basefees_mean",
                                       data=list(data["basefees_stats"]["basefees_mean"].values()),
                                       compression="gzip")
    f.create_dataset("gas", data=data["basefees_data"]["gas"], compression="gzip")
    f.create_dataset("call_data", data=data["basefees_data"]["call_data"], compression="gzip")

    f.create_dataset("mempool_sizes",data=data["mempools_data"]["mempool_sizes"] ,compression="gzip")
    #

    f.close()
    print("Saving hdf5 as " + filename + ".hdf5")

def save_figure(data,filename,filepath,iterations=None):
    plt.rcParams["figure.figsize"] = (15,10)
    if iterations is None:
        plt.title("Basefee over Time")
    else:
        plt.title("Basefee over Time. "+"Number of iterations: "+str(iterations))
    plt.xlabel("Block Number")
    plt.ylabel("Basefee (in Gwei)")
    plt.plot(data["basefees_data"]["gas"], label="gas")
    basefees_data_space = [x + 1 for x in data["basefees_data"]["call_data"]]
    plt.plot(basefees_data_space, label="call_data")
    plt.legend(loc="upper left")
    plt.savefig(filepath + filename + ".png")
    print("Saving figure as " + filename + ".png")

if __name__ == "__main__":
    if "cluster" in socket.gethostname():  # cluster
        # Initialize variables
        call_data_standard_value_input = int(sys.argv[1])
        call_data_learning_rate = str(sys.argv[2])
        a, b = call_data_learning_rate.split("/")
        call_data_learning_rate = int(a) / int(b)

        call_data_target_limit = int(sys.argv[3])
        call_data_max_limit = call_data_target_limit*2
        step_count = int(sys.argv[4])
        direc = str(sys.argv[5])
        # Initialize directory
        parent_dir = "/home/yteoh/camcos_results/" + direc +"/"
        if not os.path.exists(parent_dir):
            try:
                os.mkdir(parent_dir)
            except FileExistsError:
                print("Directory already exists")

        data_dir = "/home/yteoh/camcos_results/" + direc + "/data/"
        image_dir = "/home/yteoh/camcos_results/" + direc + "/figures/"

        # Disable figure showing
        import matplotlib
        matplotlib.use('qtagg')

    else:  # local machine
        # Initialize variables
        call_data_standard_value_input = 25
        call_data_learning_rate = 1.0 / 8
        call_data_target_limit = 25000
        call_data_max_limit = call_data_target_limit * 2
        step_count = 10
        # Initialize directory
        data_dir = "/Users/teohyikhaw/Documents/camcos_results/testing_file/data/"
        image_dir = "/Users/teohyikhaw/Documents/camcos_results/testing_file/figures/"

    if not os.path.exists(data_dir):
        try:
            os.mkdir(data_dir)
        except FileExistsError:
            print("File already exists")
    if not os.path.exists(image_dir):
        try:
            os.mkdir(image_dir)
        except FileExistsError:
            print("File already exists")

    # Basefee initialization
    bf_standard_value = 38.100002694
    bf_standard = Basefee(1.0 / 8, 15000000, 30000000, bf_standard_value)

    call_data_standard_value = call_data_standard_value_input
    call_data_standard = Basefee(call_data_learning_rate, call_data_target_limit, call_data_max_limit, call_data_standard_value)

    # Simulator initialization
    j_r = JointResources(["gas", "call_data"], bf_standard, call_data_standard)
    demand = Demand(2000, 0, 400, j_r)
    sim = Simulator(demand)

    basefees_data, block_data, mempools_data, basefees_stats = sim.simulate(step_count)
    data = {
        "basefees_data": basefees_data,
        "block_data": block_data,
        "mempools_data": mempools_data,
        "basefees_stats": basefees_stats,
    }

    attributes = {
        "resources": sim.resources,
        "resource_package":str(sim.resource_package.resource_behavior),
        "gas_bf_standard_value" : bf_standard_value,
        "gas_d":sim.basefee["gas"].d,
        "gas_target_limit": sim.basefee["gas"].target_limit,
        "gas_max_limit": sim.basefee["gas"].max_limit,
        "call_data_standard_value": call_data_standard_value_input,
        "call_data_d":call_data_learning_rate,
        "call_data_target_limit": call_data_target_limit,
        "call_data_max_limit":call_data_max_limit,
        "step_count":step_count,
        "init_txs":sim.demand.init_txns,
        "txns_per_turn":sim.demand.txns_per_turn
    }

    uniqueid = str(uuid.uuid1()).rsplit("-")[0]
    filename = "d-{0:.4f}-call_data_target-{1:d}-uuid-{uuid}".format(call_data_learning_rate,call_data_target_limit,uuid=uniqueid)

    save_simulation(data,attributes,filename,data_dir)
    save_figure(data,filename,image_dir)