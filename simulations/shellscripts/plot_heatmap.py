import seaborn as sns
import numpy as np
import h5py
import os

if __name__ == "__main__":
    # Initialize variables
    call_data_standard_value_input = 25
    call_data_learning_rate = 1.0 / 8
    call_data_target_limit = 25000
    call_data_max_limit = call_data_target_limit * 2
    step_count = 10
    # Initialize directory
    data_dir = "/Users/teohyikhaw/Documents/camcos_results/final_result_NFT/averages/"
    image_dir = "/Users/teohyikhaw/Documents/camcos_results/final_result_NFT/averaged_figures/"

    # learning_rates = [1/13, 1/11,1/8, 3/8, 5/8]
    target_limits = [72500, 75000, 77500, 90000]
    learning_rates_plot = ["5/8", "3/8" ,"1/8","1/11","1/13"]
    learning_rates = []
    for i in learning_rates_plot:
        a, b = i.split("/")
        learning_rates.append(int(a) / int(b))
    heatmap = False # set to false to plot individual grid_plot

    variance_gas = np.zeros((len(learning_rates),len(target_limits)))
    variance_call_data = np.zeros((len(learning_rates), len(target_limits)))

    # This is for looping through all basefee plots
    import matplotlib.pyplot as plt
    if not heatmap:
        fig, axs = plt.subplots(len(learning_rates),len(target_limits),sharex=True, sharey=True)

    x = 0
    y = 0

    for d in learning_rates:
        for t_lim in target_limits:

            filename_search = "d-{0:.4f}-call_data_target-{1:d}".format(d, t_lim)
            # filename_search = "call_data-target-{0:d}-max-{1:d}-d-{2:.4f}".format(t_lim,t_lim*2,d)

            for filename in os.listdir(data_dir):
                if filename_search in filename:
                    f = h5py.File(data_dir + filename, "r")
                    variance_gas[learning_rates.index(d)][target_limits.index(t_lim)] = list(f["basefees_stats"]["basefees_variance"])[0]
                    variance_call_data[learning_rates.index(d)][target_limits.index(t_lim)] = \
                    list(f["basefees_stats"]["basefees_variance"])[1]

                    if not heatmap:
                        p1 = axs[x,y].plot(list(f["gas"]),linewidth=0.6)
                        p2 = axs[x, y].plot(list(f["call_data"]),linewidth=0.6)


                    y+=1
                    if y == len(target_limits):
                        x += 1
                        y = 0

                    break

    # fig.legend()
    # fig.tick_params(axis='both', which='both', bottom=True, left=True)
    # fig.xticks(list(target_limits))
    # fig.yticks(list(learning_rates))


    print(variance_gas)
    print(variance_call_data)
    # import matplotlib.pyplot as plt
    if heatmap:
        sns.color_palette("hls", 8)
        sns.heatmap(variance_call_data,xticklabels=target_limits, yticklabels=learning_rates_plot,annot=True,cmap="crest")
    plt.show()