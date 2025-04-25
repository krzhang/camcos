import player
from main import Auction
from formatting import FormatPrinter

p1 = player.GaussianRangePlayer(0, 0.9, (0.75, 0.33))
p2 = player.GaussianRangePlayer(1, 0.5, (0.88, 0.42))

auction = Auction([p1, p2])
round_results, winnings, wincount = auction.run_simulation(50)

for i, result in enumerate(round_results, start=1):
    print(f"Round {i}")
    FormatPrinter({float: "%.2f"}).pprint(result)
    # from [python - pprint with custom float formats - Stack Overflow](https://stackoverflow.com/questions/44356693/pprint-with-custom-float-formats)
    print("\n")
    
print(f"Winnings: {winnings}")