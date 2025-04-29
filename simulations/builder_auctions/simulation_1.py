import player
from main import Auction
from formatting import FormatPrinter
import csv

# """""Previous result format and structure"""""""
# p1 = player.GaussianRangePlayer(0, # p1: slow bidder
#                                 (0.6, 0.8), # p1 speed: range of submit time including latency factor in mind(bids early, high latency)
#                                 (0.887, 0.417), # p1 mean and variance for bid proportion distribution
#                                 )
# p2 = player.ReactiveGaussianRangePlayer(1, # p2: fast bidder
#                                         (0.6, 0.8), # p2 speed: range of submit time(bids later, low latency)
#                                         (0.894, 0.595), # p2 mean and variance for bid proportion distribution
#                                         (0.887, 0.417) # p1's bid proportion distribution known to p2
#                                         )

# auction = Auction([p1, p2])
# round_results, winnings = auction.run_simulation(1000000)

# for i, result in enumerate(round_results, start=1):
#     print(f"Round {i}")
#     FormatPrinter({float: "%.3f"}).pprint(result)
#     # from [python - pprint with custom float formats - Stack Overflow](https://stackoverflow.com/questions/44356693/pprint-with-custom-float-formats)
#     print("\n")

# print(f"Winnings: {winnings}")
# """"""""""""""""""""""""""""""""""

# speeds for players for grid sim
p1_speeds = [(0.0, 0.4), (0.05, 0.45), (0.1, 0.5), (0.15, 0.55), (0.2, 0.6)]
p2_speeds = [(0.2, 0.6), (0.25, 0.65), (0.3, 0.7), (0.35, 0.75), (0.4, 0.8)]

# saving as csv file
with open('grid_simulation_results.csv', mode = 'w', newline = '') as file:
    writer = csv.writer(file)
    writer.writerow(["p1_speed", "p2_speed", "p1_winning%_over_total", "p2_winning%_over_total", "winning_gap"])

    # loop over grid
    for p1_speed in p1_speeds:
        for p2_speed in p2_speeds:
            p1 = player.GaussianRangePlayer(0, # p1: slow bidder
                                p1_speed, # p1 speed: range of submit time including latency factor in mind(bids early, high latency)
                                (0.75, 0.33), # p1 mean and variance for bid proportion distribution
                                )
            p2 = player.ReactiveGaussianRangePlayer(1, # p2: fast bidder
                                                    p2_speed, # p2 speed: range of submit time(bids later, low latency)
                                                    (0.88, 0.42), # p2 mean and variance for bid proportion distribution
                                                    (0.75, 0.33) # p1's bid proportion distribution known to p2
                                                    )
            auction = Auction([p1,p2])
            round_results, winnings = auction.run_simulation(100000)

            p1_win, p2_win = winnings
            total = p1_win + p2_win

            p1_winprop = (p1_win / total) * 100
            p2_winprop = (p2_win / total) * 100
            winning_gap = p1_winprop - p2_winprop

            writer.writerow([p1_speed, p2_speed, p1_winprop, p2_winprop, winning_gap])
