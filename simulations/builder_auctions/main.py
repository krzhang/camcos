from auction import Auction
from player import RangePlayer
import random

### ====== Configuration ====== ###

print_settings = True
print_first_n_rounds = True
n_rounds_to_print = 5

num_players = 10
num_reactive = 5

# Player parameter ranges
speed_range_reactive = (0.2, 0.3), (0.6, 0.7)
speed_range_nonreactive = (0.0, 0.1), (0.2, 0.3)
bid_range_reactive = (0.91, 0.39)
bid_range_nonreactive = (0.86, 0.26)

cutoff_time_range = (0.6, 0.7)
num_rounds = 216000

### ====== Generate Players ====== ###

players = []

# Non-reactive players
for i in range(num_players - num_reactive):
    speed = (
        random.uniform(*speed_range_nonreactive[0]),
        random.uniform(*speed_range_nonreactive[1])
    )
    bid_range = (
        random.uniform(bid_range_nonreactive[0] - bid_range_nonreactive[1],
                       bid_range_nonreactive[0] + bid_range_nonreactive[1]),
        bid_range_nonreactive[1]
    )
    players.append(RangePlayer(i, speed, bid_range, reactive=False))

# Reactive players
for i in range(num_players - num_reactive, num_players):
    speed = (
        random.uniform(*speed_range_reactive[0]),
        random.uniform(*speed_range_reactive[1])
    )
    bid_range = (
        random.uniform(bid_range_reactive[0] - bid_range_reactive[1],
                       bid_range_reactive[0] + bid_range_reactive[1]),
        bid_range_reactive[1]
    )
    players.append(RangePlayer(i, speed, bid_range, reactive=True))

pid_to_index = {p.player_id: i for i, p in enumerate(players)}

### ====== Run Simulation ====== ###

auction = Auction(players, cutoff_time_range)
round_results, winnings = auction.run_simulation(num_rounds)

### ====== Print First N Rounds ====== ###

if print_first_n_rounds:
    print(f"\n===== First {n_rounds_to_print} Round(s) Details ======")
    for i, round_data in enumerate(round_results[:n_rounds_to_print]):
        cutoff_time = round_data["cutoff_time"]
        print(f"\n--- Round {i + 1} --- Cutoff Time: {cutoff_time:.4f}")
        winner_info = round_data["winner"]
        if winner_info:
            winner_id = winner_info[0]
            winner_type = "Reactive" if next(p for p in players if p.player_id == winner_id).reactive else "Non-Reactive"
            print(f"Winner: P{winner_id} ({winner_type}) | Bid: {winner_info[1]:.4f} | Profit: {winner_info[2]:.4f}")
        else:
            print("No winner this round.")

        print(f"{'ID':<4} {'Type':<14} {'Valuation':<10} {'Bid':<10} {'Submit Time':<13} {'Status'}")
        print("-" * 60)
        for p in players:
            pid = p.player_id
            val = round_data["valuations"][pid]
            _, bid, submit_by = next((a[0].player_id, a[1], round_data["submit_bys"][a[0].player_id])
                                     for a in round_data["actions"] if a[0].player_id == pid)
            status = "ON TIME" if submit_by < cutoff_time else "LATE"
            typ = "Reactive" if p.reactive else "Non-Reactive"
            print(f"P{pid:<3} {typ:<14} {val:<10.4f} {bid:<10.4f} {submit_by:<13.4f} {status}")

### ====== Final Profit Summary ====== ###

# Count number of wins per player
win_counts = [0] * len(players)
for r in round_results:
    winner = r["winner"]
    if winner:
        win_counts[pid_to_index[winner[0]]] += 1

sorted_players = sorted(
    [(p.player_id, winnings[pid_to_index[p.player_id]], win_counts[pid_to_index[p.player_id]],
      'Reactive' if p.reactive else 'Non-Reactive', p.speed, p.range[0], p.range[1])
     for p in players],
    key=lambda x: x[1], reverse=True
)

print("\n===== Players Sorted by Profit =====")
print(f"{'ID':<4} {'Type':<14} {'Wins':<6} {'Profit':<10} {'Speed Range':<15} {'Mean':<8} {'StD'}")
print("-" * 80)
for pid, profit, wins, typ, speed, mean, std in sorted_players:
    speed_str = f"({speed[0]:.3f}, {speed[1]:.3f})"
    print(f"P{pid:<3} {typ:<14} {wins:<6} {profit:<10.3f} {speed_str:<15} {mean:<8.3f} {std:.3f}")

### ====== Print Settings ====== ###

if print_settings:
    print("\n======= Simulation Settings =======")
    print(f"Total Players: {num_players}")
    print(f"Reactive Players: {num_reactive}")
    print(f"Reactive Speed: {speed_range_reactive}")
    print(f"Reactive Bid Range: {bid_range_reactive}")
    print(f"Non-Reactive Speed: {speed_range_nonreactive}")
    print(f"Non-Reactive Bid Range: {bid_range_nonreactive}")
    print(f"Cutoff Time Range: {cutoff_time_range}")
    print(f"Simulation Rounds: {num_rounds}")
    print("===================================\n")
