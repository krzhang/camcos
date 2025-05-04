from auction import Auction
from player_setup import generate_players
from player import *

### ====== Configuration ====== ###

## Set to True to print configuration settings
print_settings = True

# Assign number of players and how many are reactive gaussian players, the rest will be regular gaussian players
num_players = 10
num_reactive = 5

## Gaussian player settings
gaussian_speed_min_range = (0.0, 0.2)
gaussian_speed_max_range = (0.2, 0.6)
gaussian_bid_prop_mean_range = (0.75, 0.95)
gaussian_bid_prop_std_range = (0.3, 0.5)

## Reactive Gaussian player settings
reactive_speed_min_range = (0.3, 0.5)
reactive_speed_max_range = (0.6, 0.9)
reactive_bid_prop_mean_range = (0.85, 0.95)
reactive_bid_prop_std_range = (0.2, 0.4)
reactive_others_mean_range = gaussian_bid_prop_mean_range
reactive_others_std_range = gaussian_bid_prop_std_range

# Auction settings
cutoff_time_range = (0.9, 1.0)
num_rounds = 100000

### ====== Run Simulation ====== ###

# Generate players
players = generate_players(
    num_players,
    num_reactive,
    gaussian_speed_min_range,
    gaussian_speed_max_range,
    gaussian_bid_prop_mean_range,
    gaussian_bid_prop_std_range,
    reactive_speed_min_range,
    reactive_speed_max_range,
    reactive_bid_prop_mean_range,
    reactive_bid_prop_std_range,
    reactive_others_mean_range,
    reactive_others_std_range
)

# Run auction
auction = Auction(players, cutoff_time_range)
round_results, winnings = auction.run_simulation(num_rounds)

# Count number of wins per player
win_counts = [0] * len(players)
for round_data in round_results:
    winner_info = round_data["winner"]
    if winner_info is not None:
        win_counts[winner_info[0]] += 1

### ====== Display Sorted Results ====== ###

# Sort the players by their winnings and include necessary details
sorted_players = sorted(
    [(p_id, winnings[p_id], win_counts[p_id],
      'Gaussian' if isinstance(player, GaussianRangePlayer) else 'Reactive',
      player.speed, player.range[0], player.range[1], 
      player.others_range[0] if isinstance(player, ReactiveGaussianRangePlayer) else None,
      player.others_range[1] if isinstance(player, ReactiveGaussianRangePlayer) else None) 
     for p_id, player in enumerate(players)],
    key=lambda x: x[1], reverse=True
)

# Print sorted results
print("\n==== Players Sorted by Winnings ====")
for p_id, win_amt, win_count, strat, speed, bid_mean, bid_std, others_mean, others_std in sorted_players:
    print(f"  Player {p_id} | {strat} | Wins: {win_count:5d} | Winnings: {win_amt:.4f} | "
          f"Speed: ({speed[0]:.3f}, {speed[1]:.3f}) | "
          f"Mean: {bid_mean:.3f} | Stddev: {bid_std:.3f}", end="")
    if others_mean is not None:
        print(f" | Others' Mean: {others_mean:.3f} | Others' Stddev: {others_std:.3f}")
    else:
        print()

### ====== Display Settings (Optional) ====== ###

if print_settings:
    print("\n======= Simulation Settings =======")
    print(f"Number of Players: {num_players}")
    print(f"Number of Reactive Players: {num_reactive}")
    print(f"Gaussian Speed Range: min {gaussian_speed_min_range}, max {gaussian_speed_max_range}")
    print(f"Gaussian Bid Prop Mean Range: {gaussian_bid_prop_mean_range}")
    print(f"Gaussian Bid Prop Std Range: {gaussian_bid_prop_std_range}")
    print(f"Reactive Speed Range: min {reactive_speed_min_range}, max {reactive_speed_max_range}")
    print(f"Reactive Bid Prop Mean Range: {reactive_bid_prop_mean_range}")
    print(f"Reactive Bid Prop Std Range: {reactive_bid_prop_std_range}")
    print(f"Reactive Knowledge of Others (Mean Range): {reactive_others_mean_range}")
    print(f"Reactive Knowledge of Others (Std Range): {reactive_others_std_range}")
    print(f"Cutoff Time Range: {cutoff_time_range}")
    print(f"Simulation Rounds: {num_rounds}")
    print("===================================\n")