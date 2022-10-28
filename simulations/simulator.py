import copy
from abc import abstractmethod

import numpy as np
import pandas as pd
import random

import oracle
import os
import h5py
import matplotlib.pyplot as plt
import uuid
from scipy import stats

INFTY = 3000000
MAX_LIMIT = 8000000


# This is for the X+Y method of doing resources instead of Z=X+Y

class Resource():
    # maybe have better docstrings?
    def __init__(self, name, distribution, alpha, beta, proportionLimit=None, lowerLimit=None):
        self.name = name
        self.distribution = distribution
        self.alpha = alpha
        self.beta = beta
        self.proportionLimit = proportionLimit
        self.lowerLimit = lowerLimit

    @abstractmethod
    def generate(self):
        pass

    def __str__(self):
        return self.name




class Demand():
    """
  class for creating a demand profile. A demand profile consists of (in lock-step)

  1) a sequence of valuations
  2) a sequence of gas limits
  3) a sequence of resources
  """

    def __init__(self, init_txns, txns_per_turn, step_count, basefee_init, resources=None):
        self.valuations = []
        self.limits = []
        self.step_count = step_count
        self.resources = resources

        # Check if resources is a list of class resources
        if resources is not None:
            assert isinstance(resources, list)
            for i in resources:
                assert (isinstance(i, Resource))

        for i in range(step_count + 1):
            # we add 1 since there's just also transactions to begin with
            if i == 0:
                txn_count = init_txns
            else:
                txn_count = random.randint(50, txns_per_turn * 2 - 50)

            # the mean for gamma(k, \theta) is k\theta, so the mean is a bit above 1.
            # note we use the initial value as a proxy for a "fair" basefee; we don't want people to
            # arbitrarily follow higher basefee, then it will spiral out of control
            # in particular, these people don't use a price oracle!

            self.valuations.append(np.random.gamma(20.72054, 1 / 17.49951, txn_count))

            # Previous code
            if resources is None:
                # pareto distribution with alpha 1.42150, beta 21000 (from empirical results)
                _limits_sample = (np.random.pareto(1.42150, txn_count) + 1) * 21000
                _limits_sample = [min(l, MAX_LIMIT) for l in _limits_sample]
                self.limits.append(_limits_sample)
            else:
                self.limits.append([tuple(resource.generate() for resource in resources) for x in range(txn_count)])


class Basefee():

    def __init__(self, d, target_limit, max_limit, value=0.0):
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
        self.value = self.value * (1 + self.d * ((gas - self.target_limit) / self.target_limit))


class Simulator():
    """ Multidimensional EIP-1559 simulator. """

    def __init__(self, basefee, resources, ratio, resource_behavior="INDEPENDENT", knapsack_solver=None):
        """
    [ratio]: example (0.7, 0.3) would split the [basefee] into 2 basefees with those
    relative values
    """
        assert len(ratio) == len(resources)
        resources = [str(x) for x in resources]  # ensures everything is a string
        self.resources = resources
        self.dimension = len(resources)  # number of resources
        self.resource_behavior = resource_behavior

        if knapsack_solver is None:
            self.knapsack_solver = "greedy"
        self.knapsack_solver = knapsack_solver

        # everything else we use is basically a dictionary indexed by the resource names
        self.ratio = {resources[i]: ratio[i] for i in range(self.dimension)}
        self.basefee = {}
        self.basefee_init = basefee.value
        for r in self.resources:
            self.basefee[r] = basefee.scaled_copy(self.ratio[r])

        self.mempool = pd.DataFrame([])

    # def total_bf(self):
    #   return self.basefee[0].value + self.basefee[1].value

    def _twiddle_ratio(self):
        """ given a ratio, twiddle the ratios a bit"""
        ratio = self.ratio
        new_ratios = {x: random.uniform(0.0, ratio[x]) for x in ratio}
        normalization = sum(new_ratios[x] for x in new_ratios)
        newer_ratios = {x: new_ratios[x] / normalization for x in ratio}
        return newer_ratios

    def update_mempool(self, demand, t):
        """
    Make [txn_number] new transactions and add them to the mempool
    """

        # checks if resources are manually placed in
        if demand.resources is not None:
            self.resource_behavior = "SEPARATED"

        # the valuations and gas limits for the transactions. Following code from
        # 2021S
        prices = {}

        _valuations = demand.valuations[t]
        txn_count = len(_valuations)

        for r in self.resources:
            prices[r] = [self.basefee_init * v for v in _valuations]

        limits = {}
        _limits_sample = demand.limits[t]

        if self.resource_behavior == "CORRELATED":
            for r in self.resources:
                limits[r] = [min(g * self.ratio[r], self.basefee[r].max_limit)
                             for g in _limits_sample]
            # this is completely correlated, so it really shouldn't affect basefee behavior
        elif self.resource_behavior == "INDEPENDENT":
            new_ratios = self._twiddle_ratio()
            for r in self.resources:
                limits[r] = [min(g * new_ratios[r], self.basefee[r].max_limit)
                             for g in _limits_sample]
        else:
            # assert self.resource_behavior == "SEPARATED"
            # Copy over generated values from demand
            for r in range(len(self.resources)):
                limits[self.resources[r]] = [_limits_sample[i][r] for i in range(len(_limits_sample))]

        # store each updated mempool as a DataFrame. Here, each *row* will be a transaction.
        # we will start with 2*[dimension] columns corresponding to prices and limits, then 2
        # more columns for auxiliary data

        total_values = [sum([prices[r][i] * limits[r][i] for r in self.resources]) for
                        i in range(txn_count)]

        data = []
        for r in self.resources:
            data.append((r + " price", prices[r]))
            data.append((r + " limit", limits[r]))
        data.append(("time", t))  # I guess this one just folds out to all of them?
        data.append(("total_value", total_values))
        data.append(("profit", 0))
        txns = pd.DataFrame(dict(data))

        self.mempool = pd.concat([self.mempool, txns])

    def _compute_profit(self, tx):
        """
    Given a txn (DataFrame), compute the profit (given current basefees). This is the difference
    between its [total_value] and the burned basefee

    """
        txn = tx.to_dict()
        burn = sum([txn[r + " limit"] * self.basefee[r].value for r in self.resources])
        return tx["total_value"] - burn

    def fill_block(self, time, method=None):
        if method is None:
            method = "greedy"

        """ create a block greedily from the mempool and return it"""
        block = []
        block_size = {r: 0 for r in self.resources}
        block_max = {r: self.basefee[r].max_limit for r in self.resources}
        block_min_tip = {r: INFTY for r in self.resources}
        # the minimal tip required to be placed in this block

        # we now do a greedy algorithm to fill the block.

        # 1. we sort transactions in each mempool by total value in descending order

        self.mempool['profit'] = self.mempool.apply(self._compute_profit, axis=1)
        if method == "greedy":
            self.mempool = self.mempool.sort_values(by=['profit'],
                                                    ascending=False).reset_index(drop=True)
        # randomly choose blocks by not sorting them
        elif method == "random":
            self.mempool = self.mempool.sample(frac=1).reset_index(drop=True)

        # 2. we keep going until we get stuck (basefee too high, or breaks resource limit)
        #    Since we might have multiple resources and we don't want to overcomplicate things,
        #    our hack is just to just have a buffer of lookaheads ([patience], which decreases whenever
        #    we get stuck) and stop when we get stuck.
        patience = 10
        included_indices = []
        for i in range(len(self.mempool)):
            tx = self.mempool.iloc[i, :]
            txn = tx.to_dict()
            # this should give something like {"time":blah, "total_value":blah...
            # TODO: should allow negative money if it's worth a lot of money in total
            if (any(txn[r + " limit"] + block_size[r] > block_max[r] for r in self.resources) or
                    txn["profit"] < 0):
                if patience == 0:
                    break
                else:
                    patience -= 1
            else:
                block.append(txn)
                included_indices.append(i)
                # faster version of self.mempool = self.mempool.iloc[i+1:, :]
                for r in self.resources:
                    block_size[r] += txn[r + " limit"]
                    if txn[r + " price"] - self.basefee[r].value < block_min_tip[r]:
                        block_min_tip[r] = txn[r + " price"] - self.basefee[r].value

        self.mempool.drop(included_indices, inplace=True)
        # block_wait_times = [time - txn["time"] for txn in block]
        # self.wait_times.append(block_wait_times)

        return block, block_size, block_min_tip

    def simulate(self, demand):
        """ Run the simulation for n steps """

        # initialize empty dataframes
        blocks = []
        mempools = []
        new_txn_counts = []
        used_txn_counts = []
        self.oracle = oracle.Oracle(self.resources, self.ratio, self.basefee_init)

        basefees = {r: [self.basefee[r].value] for r in self.resources}
        limit_used = {r: [] for r in self.resources}
        min_tips = {r: [] for r in self.resources}
        # initialize mempools
        self.update_mempool(demand, 0)  # the 0-th slot for demand is initial transactions

        step_count = len(demand.valuations) - 1

        # iterate over n blocks
        for i in range(step_count):
            # fill blocks from mempools
            new_block, new_block_size, new_block_min_tips = self.fill_block(i, method=self.knapsack_solver)
            blocks += [new_block]
            self.oracle.update(new_block_min_tips)

            # update mempools

            for r in self.resources:
                self.basefee[r].update(new_block_size[r])
                basefees[r] += [self.basefee[r].value]
                limit_used[r].append(new_block_size[r])
                min_tips[r].append(new_block_min_tips[r])

            # # Commented: save mempools (expensive!)
            # # if we do use them, this creates a copy; dataframes and lists are mutable
            # mempools += [pd.DataFrame(self.mempool)]

            # mempools_bf += [self.mempool[self.mempool['gas price'] >= self.total_bf()]]
            # what does this do??

            # new txns before next iteration
            # we want supply to match demand;
            # right now target gas is 15000000, each transaction is on average 2.42*21000 = 52000 gas,
            # so we should shoot for 300 transactions per turn

            used_txn_counts.append(len(new_block))

            self.update_mempool(demand, i + 1)  # we shift by 1 because of how demand is indexed
            new_txns_count = len(demand.valuations[i + 1])

            new_txn_counts.append(new_txns_count)

        block_data = {"blocks": blocks,
                      "limit_used": limit_used,
                      "min_tips": min_tips}
        mempool_data = {"new_txn_counts": new_txn_counts,
                        #                    "mempools":mempools,
                        "used_txn_counts": used_txn_counts}
        return basefees, block_data, mempool_data


def generate_simulation_data(simulator, demand, num_iterations):
    """
  This function generates multiple iterations of the simulation
  :param simulator: Accepts Simulator object
  :param demand: Accepts Demand object
  :param num_iterations: int of number of times it will run
  :returns average of basefees and an array of dictionary of basefees, block_data and mempool_data from each iteration
  """
    # Array of arrays of the average of each resource
    averages = [[0 for x in range(demand.step_count + 1)] for i in range(simulator.dimension)]
    # Array of dictionary of basefees, block_data and mempool_data from each iteration
    outputs = []

    for i in range(num_iterations):
        # New simulator each time so it doesn't build on previous simulator object
        new_simulator = copy.deepcopy(simulator)
        basefees_data, block_data, mempools_data = new_simulator.simulate(demand)
        outputs.append(
            {"basefees_data": basefees_data, "block_data": block_data, "mempools_data": mempools_data})

        # Shift entire y-axis by 1 unit, so it will be visible on plot in case it overlaps
        shift_count = 0
        for i in range(new_simulator.dimension):
            # Pre-process data to make it look visible on plot by shifting y-value by 1
            basefees_data[str(new_simulator.resources[i])] = [i + shift_count for i in
                                                              basefees_data[str(new_simulator.resources[i])]]
            averages[i] = np.add(averages[i], basefees_data[str(new_simulator.resources[i])])
            shift_count += 1

    # Take average of all iterations
    for i in range(len(averages)):
        averages[i] = [x / num_iterations for x in averages[i]]

    averaged_data = {simulator.resources[key]: averages[key] for key in range(simulator.dimension)}
    return averaged_data, outputs


def save_simulation_data(data: dict, filename, filetype=None, filepath=None):
    """
    Saves simulation data into hdf5, csv or both
    :param data: A dictionary of {resource:data}
    :param filename: String of filename, should include uuid of iteration
    :param filetype: String as "hdf5", "csv" or "hdf5+csv" which determines the output file format
    :param filepath: String of directory
    """
    # Input checking and processing
    if filetype is None:
        filetype = "hdf5"
    assert filetype == "hdf5" or filetype == "csv" or filetype == "hdf5+csv"
    if filepath is None:
        filepath = os.getcwd()
        if not os.path.exists(filepath):
            os.mkdir(filepath)
    if not os.path.exists(filepath + "/data/"):
        os.mkdir(filepath + "/data/")

    if filetype == "hdf5" or filetype == "hdf5+csv":
        f = h5py.File(filepath + "/data/" + filename + ".hdf5", "w")
        for key in data:
            f.create_dataset(str(key), data=data[key], compression="gzip")
        f.close()
        print("Saving hdf5 as " + filename + ".hdf5")
    if filetype == "csv" or filetype == "hdf5+csv":
        df = pd.DataFrame({str(key): data[key] for key in data})
        df.to_csv(filepath + "/data/" + filename + ".csv", index=False)
        print("Saving csv as " + filename + ".csv")


def plot_simulation(data: dict, filename, title, x_label, y_label, show=False, filepath=None):
    """
    Generates plots given simulation data and saves it into filepath directory
    :param data: A dictionary of {resource:data}
    :param filename: String of filename, should include uuid of iteration that matches with generated hdf5 or csv file
    :param title: Title of plot
    :param x_label: Label for x-axis
    :param y_label: Label for y-axis
    :param show: Whether to display by calling plt.show() or not
    :param filepath: String of directory
    """
    if filepath is None:
        filepath = os.getcwd()
        if not os.path.exists(filepath):
            os.mkdir(filepath)
    if not os.path.exists(filepath + "/figures/"):
        os.mkdir(filepath + "/figures/")
    plt.rcParams["figure.figsize"] = (15, 10)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    for x in data:
        plt.plot(data[x], label=str(x))
    plt.legend(loc="upper left")
    plt.savefig(filepath + "/figures/" + filename + ".png")
    print("Saving figure as " + filename)
    if show:
        plt.show()
    plt.cla()


def run_simulations(simulator, demand, num_iterations, filetype=None, filepath=None):
    """
    This function creates data, saves it and plots the average and all individual plots
    :param simulator: Accepts Simulator object
    :param demand: Accepts Demand object
    :param num_iterations: int of number of iterations averaged over
    :param filetype: Will be passed into generate_simulation_data
    :param filepath: Will be passed into generate_simulation_data
    :returns averaged_data: Average of basefees of each resource over num_iterations
    """
    averaged_data, outputs = generate_simulation_data(simulator, demand, num_iterations)
    for count in range(len(outputs)):
        uniqueid = str(uuid.uuid1()).rsplit("-")[0]
        filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-{uuid}".format(simulator.dimension,
                                                                                   x=simulator.resource_behavior,
                                                                                   y=simulator.knapsack_solver,
                                                                                   uuid=uniqueid)
        save_simulation_data(outputs[count]["basefees_data"], filename, filetype, filepath)
        plot_simulation(outputs[count]["basefees_data"],filename,"Basefee over Time","Block Number","Basefee (in Gwei)",show=False,filepath=filepath)

    # Plot and save averaged data
    filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-averaged".format(2, x=simulator.resource_behavior,
                                                                                 y=simulator.knapsack_solver)
    save_simulation_data(averaged_data, filename, filetype, filepath)
    plot_simulation(averaged_data,filename,"Basefee over Time. {0:d} iterations".format(num_iterations),"Block Number","Basefee (in Gwei)",show=True,filepath=filepath)
    return averaged_data