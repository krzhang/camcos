import player
from main import Auction
from formatting import FormatPrinter

p1 = player.GaussianRangePlayer(0, # p1: slow bidder
                                (0.0, 0.7), # p1 speed: range of submit time including latency factor in mind(bids early, high latency)
                                (0.75, 0.33), # p1 mean and variance for bid proportion distribution
                                )
p2 = player.ReactiveGaussianRangePlayer(1, # p2: fast bidder
                                        (0.5, 0.8), # p2 speed: range of submit time(bids later, low latency)
                                        (0.88, 0.42), # p2 mean and variance for bid proportion distribution
                                        (0.75, 0.33) # p1's bid proportion distribution known to p2
                                        )

auction = Auction([p1, p2])
round_results, winnings = auction.run_simulation(50)

for i, result in enumerate(round_results, start=1):
    print(f"Round {i}")
    FormatPrinter({float: "%.3f"}).pprint(result)
    # from [python - pprint with custom float formats - Stack Overflow](https://stackoverflow.com/questions/44356693/pprint-with-custom-float-formats)
    print("\n")
    
print(f"Winnings: {winnings}")