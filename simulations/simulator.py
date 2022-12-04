import copy

import numpy as np
import pandas as pd
import random

import oracle
import resources
import os
import h5py
import uuid
from scipy import stats
from resources import ResourcePackage
from constants import MAX_LIMIT, INFTY
from heapq import heapify, heappush, heappop


class Demand():
    """
  class for creating a demand profile. A demand profile consists of (in lock-step)

  1) a sequence of valuations
  2) a sequence of gas limits
  3) a sequence of resources
  """

    def __init__(self, init_txns,t, txns_per_turn, resources: ResourcePackage):
        self.init_txns = init_txns
        self.valuations = []
        self.limits = {}
        self.t = t
        self.txns_per_turn = txns_per_turn
        self.resources = resources


    def update(self,t):
        """
        Updates a new list of transactions and stores them in valuations and limits
        :param t: int of time
        """
        self.t = t
        if self.t == 0:
            txn_count = self.init_txns
        else:
            txn_count = random.randint(50, self.txns_per_turn * 2 - 50)

        # the mean for gamma(k, \theta) is k\theta, so the mean is a bit above 1.
        # note we use the initial value as a proxy for a "fair" basefee; we don't want people to
        # arbitrarily follow higher basefee, then it will spiral out of control
        # in particular, these people don't use a price oracle!

        self.valuations = np.random.gamma(20.72054, 1 / 17.49951, txn_count)
        for r in self.resources.resource_names:
            self.limits[r] = []
        for i in range(txn_count):
            generated_resource = self.resources.generate()
            for r in self.resources.resource_names:
                self.limits[r].append(generated_resource[r])

class Simulator():
    """ Multidimensional EIP-1559 simulator. """

    def __init__(self, demand:Demand, knapsack_solver="greedy",tx_decay_time = -1):
        """
    [ratio]: example (0.7, 0.3) would split the [basefee] into 2 basefees with those
    relative values
    """
        self.resource_package = demand.resources
        resources = [str(x) for x in self.resource_package.resource_names]  # ensures everything is a string
        self.resources = resources # list of the names of resources for indexing purposes
        self.dimension = len(resources)  # number of resources
        self.demand = demand
        self.split = demand.resources.split
        self.basefee = self.resource_package.basefee


        ### This section conflicts with oracle code
        if self.split:
            # One basefee for X+Y = Z method
            self.basefee_init = self.resource_package.basefee_init
            # for r in self.resources:
            #     self.basefee_init += self.resource_package.basefee[r].value
        else:
            # Dictionary of initial basefees for X+Y method
            self.basefee_init = {}
            for r in self.resources:
                self.basefee_init[r] = self.resource_package.basefee[r].value

        ### Previous method
        # self.basefee_init = 0
        # for r in self.resources:
        #     self.basefee_init += self.resource_package.basefee[r].value
        ###
        self.knapsack_solver = knapsack_solver
        self.tx_decay_time = tx_decay_time
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

    def update_mempool(self, demand: Demand, t):
        """
    Make [txn_number] new transactions and add them to the mempool
    """

        # the valuations and gas limits for the transactions. Following code from
        # 2021S
        prices = {}

        demand.update(t)
        _valuations = demand.valuations
        txn_count = len(_valuations)

        ### This section conflicts with oracle code
        if self.split:
            for r in self.resources:
                prices[r] = [self.basefee_init * v for v in _valuations]
        else:
            for r in self.resources:
                prices[r] = [self.basefee_init[r] * v for v in _valuations]
        ### Previous code
        # for r in self.resources:
        #     prices[r] = [self.basefee_init * v for v in _valuations]
        ###

        limits = demand.limits

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
        # possible choices: greedy, dp, random, backlog

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
        if method == "greedy" or method == "backlog":
            self.mempool = self.mempool.sort_values(by=['profit'],
                                                    ascending=False).reset_index(drop=True)
        # randomly choose blocks by not sorting them
        elif method == "random":
            self.mempool = self.mempool.sample(frac=1).reset_index(drop=True)

        # 2. we keep going until we get stuck (basefee too high, or breaks resource limit)
        #    Since we might have multiple resources and we don't want to overcomplicate things,
        #    our hack is just to just have a buffer of lookaheads ([patience], which decreases whenever
        #    we get stuck) and stop when we get stuck.
        included_indices = []
        if method == "dp":
            # This is the dynamic programming technique. Currently only works for 2 resources
            if self.dimension != 2:
                raise ValueError("Current method only supports 2 resources!")
            # gas array

            selected_indices = knapsack(self.resource_package.basefee["gas"].max_limit,
                                        self.mempool["gas limit"],
                                        self.mempool["call_data limit"],
                                        len(self.mempool["gas limit"]),
                                        self.resource_package.basefee["call_data"].max_limit,
                                        )
            for i in selected_indices:
                tx = self.mempool.iloc[i, :]
                txn = tx.to_dict()
                block.append(txn)
                included_indices.append(i)
                # faster version of self.mempool = self.mempool.iloc[i+1:, :]
                for r in self.resources:
                    block_size[r] += txn[r + " limit"]
                    if txn[r + " price"] - self.basefee[r].value < block_min_tip[r]:
                        block_min_tip[r] = txn[r + " price"] - self.basefee[r].value


        else:
            heap = []
            heapify(heap)
            patience = 10
            for i in range(len(self.mempool)):
                tx = self.mempool.iloc[i, :]
                txn = tx.to_dict()

                if method == "backlog" and len(heap)>0:
                    txn = heappop(heap)[1]

                # this should give something like {"time":blah, "total_value":blah...
                # TODO: should allow negative money if it's worth a lot of money in total
                if (any(txn[r + " limit"] + block_size[r] > block_max[r] for r in self.resources) or
                        txn["profit"] < 0):

                    if method == "backlog" and len(heap) > 0:
                        heappush(heap,(txn["profit"],txn))
                    included_indices.append(i)

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

    def simulate(self, step_count):
        """ Run the simulation for n steps
        :param step_count: Number of blocks to evolve by
        :return: basefees, block_data, mempool_data
        """
        demand = self.demand

        # initialize empty dataframes
        blocks = []
        mempools = []
        mempool_sizes = []
        new_txn_counts = []
        used_txn_counts = []
        # self.oracle = oracle.Oracle(self.resources, self.ratio, self.basefee_init)

        basefees = {r: [self.basefee[r].value] for r in self.resources}
        limit_used = {r: [] for r in self.resources}
        min_tips = {r: [] for r in self.resources}
        block_utilization_rate = {r: [] for r in self.resources}
        # initialize mempools
        self.update_mempool(demand, 0)  # the 0-th slot for demand is initial transactions

        # iterate over n blocks
        for i in range(step_count):
            # fill blocks from mempools
            new_block, new_block_size, new_block_min_tips = self.fill_block(i, method=self.knapsack_solver)
            blocks += [new_block]
            # self.oracle.update(new_block_min_tips)

            # update mempools

            for r in self.resources:
                self.basefee[r].update(new_block_size[r])
                basefees[r] += [self.basefee[r].value]
                limit_used[r].append(new_block_size[r])
                min_tips[r].append(new_block_min_tips[r])
                block_utilization_rate[r].append(new_block_size[r]/self.basefee[r].max_limit)

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

            mempool_sizes.append(len(self.mempool))
            self.update_mempool(demand, i + 1)  # we shift by 1 because of how demand is indexed
            new_txns_count = len(demand.valuations)
            new_txn_counts.append(new_txns_count)

            # Drop expired transactions
            if self.tx_decay_time>0:
                self.mempool = self.mempool[self.mempool["time"]>i-self.tx_decay_time]


        block_data = {"blocks": blocks,
                      "limit_used": limit_used,
                      "min_tips": min_tips,
                      "block_utilization_rate": block_utilization_rate
                      }
        mempool_data = {"new_txn_counts": new_txn_counts,
                        #                    "mempools":mempools,
                        "used_txn_counts": used_txn_counts,
                        "mempool_sizes":mempool_sizes}

        basefee_variance = {r: np.var(basefees[r]) for r in self.resources}
        basefee_mean = {r: np.mean(basefees[r]) for r in self.resources}

        basefees_stats = { "basefees_variance": basefee_variance,
                         "basefees_mean": basefee_mean,
        }

        return basefees, block_data, mempool_data, basefees_stats


def generate_simulation_data(simulator,step_count, num_iterations):
    """
  This function generates multiple iterations of the simulation
  :param simulator: Accepts Simulator object
  :param step_count: Number of blocks to evolve by
  :param num_iterations: int of number of times it will run
  :returns average of basefees and an array of dictionary of basefees, block_data and mempool_data from each iteration
  """
    # Array of arrays of the average of each resource
    averages = [[0 for x in range(step_count + 1)] for i in range(simulator.dimension)]
    # Array of dictionary of basefees, block_data and mempool_data from each iteration
    outputs = []

    for i in range(num_iterations):
        # New simulator each time so it doesn't build on previous simulator object
        new_simulator = copy.deepcopy(simulator)
        basefees_data, block_data, mempools_data = new_simulator.simulate(step_count)
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


def run_simulations(simulator,step_count, num_iterations, filetype=None, filepath=None):
    """
    This function creates data, saves it and plots the average and all individual plots
    :param simulator: Accepts Simulator object
    :param step_count: Number of blocks to evolve
    :param num_iterations: int of number of iterations averaged over
    :param filetype: Will be passed into generate_simulation_data
    :param filepath: Will be passed into generate_simulation_data
    :returns averaged_data: Average of basefees of each resource over num_iterations
    """
    averaged_data, outputs = generate_simulation_data(simulator, step_count, num_iterations)
    # Plot and save individual plots
    for count in range(len(outputs)):
        uniqueid = str(uuid.uuid1()).rsplit("-")[0]
        filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-{uuid}".format(simulator.dimension,
                                                                                   x=simulator.resource_package.resource_behavior,
                                                                                   y=simulator.knapsack_solver,
                                                                                   uuid=uniqueid)
        save_simulation_data(outputs[count]["basefees_data"], filename, filetype, filepath)
        plot_simulation(outputs[count]["basefees_data"],filename,"Basefee over Time","Block Number","Basefee (in Gwei)",show=False,filepath=filepath)

    # Plot and save averaged data
    filename = "meip_data-dimensions-{0:d}-{x}-block_method-{y}-averaged".format(2, x=simulator.resource_package.resource_behavior,
                                                                                 y=simulator.knapsack_solver)
    save_simulation_data(averaged_data, filename, filetype, filepath)
    plot_simulation(averaged_data,filename,"Basefee over Time. {0:d} iterations".format(num_iterations),"Block Number","Basefee (in Gwei)",show=True,filepath=filepath)
    return averaged_data

# Dynamic programming method for solving knapsack problem
def knapsack(W, resource_1, resource_2, n, capped_value=None):
    wt = resource_1
    val = resource_2

    # Initialize dp array
    K = [[0 for w in range(W + 1)]
         for i in range(n + 1)]

    # Build table K[][] in bottom up manner
    for i in range(n + 1):
        for w in range(W + 1):
            if i == 0 or w == 0:
                K[i][w] = 0
            elif wt[i - 1] <= w:
                K[i][w] = max(val[i - 1]
                              + K[i - 1][w - wt[i - 1]],
                              K[i - 1][w])
            else:
                K[i][w] = K[i - 1][w]

    # stores the result of Knapsack
    if capped_value is None:
        total_val = K[n][W]
    else:
        unique_list = np.unique(K)
        # Do binary search
        start = 0
        end = len(unique_list) - 1
        if (end == 0):
            return -1
        if (capped_value > unique_list[end]):
            return end

        total_val = -1
        while (start <= end):
            mid = (start + end) // 2
            if (unique_list[mid] >= capped_value):
                end = mid - 1
            else:
                total_val = mid
                start = mid + 1

    if total_val<0:
        raise ValueError("Optimized solution not found")

    w = W
    included_indices = []
    for i in range(n, 0, -1):
        if total_val <= 0:
            break
        # either the result comes from the top (K[i-1][w]) or from (val[i-1] + K[i-1] [w-wt[i-1]]) as in Knapsack
        # table. If it comes from the latter one it means the item is included.
        if total_val == K[i - 1][w]:
            continue
        else:

            # This item is included.
            included_indices.append(i-1)

            # Since this weight is included
            # its value is deducted
            total_val -= val[i - 1]
            w -= wt[i - 1]

    return included_indices