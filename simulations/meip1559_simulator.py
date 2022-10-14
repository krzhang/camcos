

import pandas as pd

class Resource():
    def __init__(self,basefee,limit, type, cost = None):
        self.basefee = basefee
        self.limit = limit
        self.type = type
        if cost is None:
            self.cost = 0
        else:
            self.cost = cost

    def update(self):
        print("")


class Block():
    def __init__(self,resources):
        self.resources = resources
        self.dimensions = len(resources)
        self.cost = 0
        for i in resources:
           self.cost += i.cost

class Simulator():
    def __init__(self,resources):
        self.resources = resources
        self.dimensions = len(resources)
        self.mempool = pd.DataFrame([])

    def update(self):
        for i in self.resources:
            i.update()

if __name__ == "__main__":
    bandwidth = Resource(15,30,"bandwidth")
    compute = Resource(15,30,"compute")
    state_access = Resource(15,30,"state_access")
    all_resources = [bandwidth, compute, state_access]

    sim = Simulator(all_resources)