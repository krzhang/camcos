import random
import player
import auction

players = []

p1 = player.RangePlayer("naive_slow", (0.3, 0.2), (0.8, 0.1), False)
p2 = player.RangePlayer("naive_fast", (0.7, 0.4), (0.8, 0.1), False)
p3 = player.RangePlayer("react_slow", (0.3, 0.2), (0.8, 0.1), True)
p4 = player.RangePlayer("react_fast", (0.7, 0.4), (0.8, 0.1), True)

players = [p1,p2,p3,p4]

auction = auction.Auction(players, (0.8, 1.0))
round_results, winnings = auction.run_simulation(5, debug=True)