import numpy as np
from single_trajectory_simulation import save_simulation,save_figure
import socket
import os
import h5py
import sys

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
        data_dir = "/home/yteoh/camcos_results/" + direc + "/data/"
        average_dir = "/home/yteoh/camcos_results/" + direc + "/averages/"
        image_dir = "/home/yteoh/camcos_results/" + direc + "/averaged_figures/"

    else:  # local machine
        # Initialize variables
        call_data_standard_value_input = 25
        call_data_learning_rate = 1.0 / 8
        call_data_target_limit = 25000
        call_data_max_limit = call_data_target_limit * 2
        step_count = 10
        # Initialize directory
        data_dir = "/Users/teohyikhaw/Documents/camcos_results/testing_file/data/"
        average_dir = "/Users/teohyikhaw/Documents/camcos_results/testing_file/averages/"
        image_dir = "/Users/teohyikhaw/Documents/camcos_results/testing_file/averaged_figures/"

    if not os.path.exists(average_dir):
        try:
            os.mkdir(average_dir)
        except FileExistsError:
            print("File already exists")
    if not os.path.exists(image_dir):
        try:
            os.mkdir(image_dir)
        except FileExistsError:
            print("File already exists")

    # Set filename search based on parameters
    filename_search = "d-{0:.4f}-call_data_target-{1:d}".format(call_data_learning_rate, call_data_target_limit)
    f = h5py.File(average_dir+filename_search+".hdf5","w")

    # parameters to be averaged
    basefees_variance = [0 for _ in range(2)]
    basefees_mean = [0 for _ in range(2)]
    gas = [0 for _ in range(step_count+1)]
    call_data = [0 for _ in range(step_count + 1)]
    mempool_sizes = [0 for _ in range(step_count)]

    count = 0
    for filename in os.listdir(data_dir):
        if filename_search in filename:
            single_instance_file = h5py.File(data_dir+filename,"r+")
            if count == 0:
                # copy over all attributes
                attributes = {str(key): single_instance_file.attrs[key] for key in single_instance_file.attrs.keys()}
            # copy and add all
            basefees_variance = np.add(basefees_variance,list(single_instance_file["basefees_stats"]["basefees_variance"]))
            basefees_mean = np.add(basefees_mean,list(single_instance_file["basefees_stats"]["basefees_mean"]))
            gas = np.add(gas, list(single_instance_file["gas"]))
            call_data = np.add(call_data, list(single_instance_file["call_data"]))
            mempool_sizes = np.add(mempool_sizes, list(single_instance_file["mempool_sizes"]))
            count+=1
    if count == 0:
        raise ZeroDivisionError("No files found!")

    basefees_variance = np.divide(basefees_variance,count)
    basefees_mean = np.divide(basefees_mean, count)
    gas = np.divide(gas, count)
    call_data = np.divide(call_data, count)
    mempool_sizes = np.divide(mempool_sizes, count)

    resources = list(attributes["resources"])

    basefees_stats = {
        "basefees_variance": {resources[r]: basefees_variance[r] for r in range(len(resources))},
        "basefees_mean":{resources[r]: basefees_mean[r] for r in range(len(resources))}
    }
    basefees_data = {
        "gas":gas,
        "call_data":call_data
    }
    mempools_data = {
        "mempool_sizes":mempool_sizes
    }

    data = {
        "basefees_data": basefees_data,
        "mempools_data": mempools_data,
        "basefees_stats": basefees_stats,
    }

    ### Extra overall basefee stats saver
    basefee_variance_overall = {
        "gas":np.var(gas),
        "call_data":np.var(call_data)
    }
    basefee_mean_overall = {
        "gas": np.mean(gas),
        "call_data": np.mean(call_data)
    }

    basefees_stats_save_overall = f.create_group("basefees_stats_overall")
    basefees_stats_save_overall.create_dataset("basefees_variance",
                                       data=list(basefee_variance_overall.values()),
                                       compression="gzip")
    basefees_stats_save_overall.create_dataset("basefees_mean",
                                       data=list(basefee_mean_overall.values()),
                                       compression="gzip")
    ###

    save_simulation(data,attributes,filename_search,average_dir)
    save_figure(data,filename_search,image_dir,count)


