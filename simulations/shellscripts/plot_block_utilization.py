

if __name__ == "__main__":
    d = 1 / 9
    t_lim = 23500
    data_dir = "/Users/teohyikhaw/Documents/camcos_results/2022_12_11/averages/"
    filename = "d-{0:.4f}-call_data_target-{1:d}.hdf5".format(d, t_lim)

    f = h5py.File(data_dir + filename, "r")

    import matplotlib.pyplot as plt
    plt.rcParams["figure.figsize"] = (15, 10)
    plt.plot(total_basefees, label="MEIP-1559")
    plt.legend()
    plt.show()
