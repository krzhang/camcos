from simulations.simulator import Basefee, Simulator
from simulations.oracle import Oracle



if __name__=="__main__":
    basefee = Basefee(10000,15000,30000)
    resource_in = ["call_data","evm"]
    ratio = [0.5,0.5]


    sim = Simulator(basefee,resource_in,ratio)
