from auction import Auction
from player_setup import generate_players
from player import *

### ====== Configuration ====== ###

## Set to True to print configuration settings
print_settings = True
## Set to True to print first n rounds
print_first_n_rounds = True
n_rounds_to_print = 5

# Assign number of players and how many are reactive gaussian players, the rest will be regular gaussian players;
# There is additional support to include different types of regular gaussian players if selected. Otherwise, can set Gaussian2 to 0 to ignore
num_players = 10
num_reactive = 5
num_gaussian2 = 1

gaussian_speed_min_range, gaussian_speed_max_range = (0.0, 0.2), (0.2, 0.6)
gaussian_bid_prop_mean_range, gaussian_bid_prop_std_range = (0.65, 0.90), (0.1, 0.2)

gaussian2_speed_min_range, gaussian2_speed_max_range = (0.1, 0.3), (0.3, 0.7)
gaussian2_bid_prop_mean_range, gaussian2_bid_prop_std_range = (0.45, 0.60), (0.1, 0.2)

reactive_speed_min_range, reactive_speed_max_range = (0.3, 0.5), (0.6, 0.9)
reactive_bid_prop_mean_range, reactive_bid_prop_std_range = (0.80, 0.90), (0.1, 0.2)
reactive_others_mean_range, reactive_others_std_range = gaussian_bid_prop_mean_range, gaussian_bid_prop_std_range

# Auction settings
cutoff_time_range = (0.75, 0.85)
num_rounds = 1000000

### ====== Run Simulation ====== ###

# Generate players
players = generate_players(
    num_players,
    num_reactive,
    num_gaussian2,
    gaussian_speed_min_range,
    gaussian_speed_max_range,
    gaussian_bid_prop_mean_range,
    gaussian_bid_prop_std_range,
    gaussian2_speed_min_range,
    gaussian2_speed_max_range,
    gaussian2_bid_prop_mean_range,
    gaussian2_bid_prop_std_range,
    reactive_speed_min_range,
    reactive_speed_max_range,
    reactive_bid_prop_mean_range,
    reactive_bid_prop_std_range,
    reactive_others_mean_range,
    reactive_others_std_range
)

pid_to_index = {p.player_id: i for i, p in enumerate(players)}

auction = Auction(players, cutoff_time_range)
round_results, winnings = auction.run_simulation(num_rounds)

### ====== Display Round Info ====== ###

if print_first_n_rounds:
    print(f"\n===== First {n_rounds_to_print} Round(s) Details ======")
    for i, round_data in enumerate(round_results[:n_rounds_to_print]):
        cutoff_time = round_data["cutoff_time"]
        print(f"\n--- Round {i + 1} --- Cutoff Time: {cutoff_time:.4f}")
        winner_info = round_data["winner"]
        if winner_info:
            winner_id = winner_info[0]
            winner_player = next(p for p in players if p.player_id == winner_id)
            if isinstance(winner_player, ReactiveGaussianRangePlayer):
                winner_type = "Reactive"
            elif isinstance(winner_player, GaussianRangePlayer2):
                winner_type = "Gaussian2"
            else:
                winner_type = "Gaussian"
            print(f"Winner: P{winner_id} ({winner_type}) | Bid: {winner_info[1]:.4f} | Profit: {winner_info[2]:.4f}")
        else:
            print("No winner this round.")

        print(f"{'ID':<4} {'Type':<9} {'Valuation':<10} {'Bid':<10} {'Submit Time':<13} {'Status'}")
        print("-" * 60)
        for p in players:
            pid = p.player_id
            val = round_data["valuations"][pid_to_index[pid]]
            _, bid, submit_by = round_data["strategies"][pid]
            status = "ON TIME" if submit_by < cutoff_time else "LATE"
            if isinstance(p, ReactiveGaussianRangePlayer):
                player_type = "Reactive"
            elif isinstance(p, GaussianRangePlayer2):
                player_type = "Gaussian2"
            else:
                player_type = "Gaussian"
            print(f"P{pid:<3} {player_type:<9} {val:<10.4f} {bid:<10.4f} {submit_by:<13.4f} {status}")

### ====== Sorted Results ====== ###

# Count number of wins per player
win_counts = [0] * len(players)
for r in round_results:
    winner = r["winner"]
    if winner:
        win_counts[pid_to_index[winner[0]]] += 1

# Sort the players by their winnings and include necessary details
sorted_players = sorted(
    [(p.player_id, winnings[pid_to_index[p.player_id]], win_counts[pid_to_index[p.player_id]],
      'Gaussian2' if isinstance(p, GaussianRangePlayer2)
      else 'Reactive' if isinstance(p, ReactiveGaussianRangePlayer)
      else 'Gaussian',
      p.speed, p.range[0], p.range[1],
      p.others_range[0] if isinstance(p, ReactiveGaussianRangePlayer) else None,
      p.others_range[1] if isinstance(p, ReactiveGaussianRangePlayer) else None)
     for p in players],
    key=lambda x: x[1], reverse=True
)

print("\n===== Players Sorted by Profit =====")
print(f"{'ID':<4} {'Type':<9} {'Wins':<6} {'Profit':<10} {'Speed Range':<15} {'Mean':<8} {'StD':<8} {'Pub. Mean':<10} {'Pub. StD'}")
print("-" * 90)
for pid, profit, wins, typ, speed, mean, std, pub_mean, pub_std in sorted_players:
    speed_str = f"({speed[0]:.3f}, {speed[1]:.3f})"
    pub_mean_str = f"{pub_mean:.3f}" if pub_mean is not None else "N/A"
    pub_std_str = f"{pub_std:.3f}" if pub_std is not None else "N/A"
    print(f"P{pid:<3} {typ:<9} {wins:<6} {profit:<10.3f} {speed_str:<15} {mean:<8.3f} {std:<8.3f} {pub_mean_str:<10} {pub_std_str}")

### ====== Print Settings ====== ###

if print_settings:
    print("\n======= Simulation Settings =======")
    print(f"Number of Players: {num_players}")
    print(f"Number of Reactive Players: {num_reactive}")
    print(f"Number of Gaussian2 Players: {num_gaussian2}")
    print(f"Gaussian Speed Range: min {gaussian_speed_min_range}, max {gaussian_speed_max_range}")
    print(f"Gaussian Bid Prop Range: mean {gaussian_bid_prop_mean_range}, std {gaussian_bid_prop_std_range}")
    print(f"Gaussian2 Speed Range: min {gaussian2_speed_min_range}, max {gaussian2_speed_max_range}")
    print(f"Gaussian2 Bid Prop Range: mean {gaussian2_bid_prop_mean_range}, std {gaussian2_bid_prop_std_range}")
    print(f"Reactive Speed Range: min {reactive_speed_min_range}, max {reactive_speed_max_range}")
    print(f"Reactive Bid Prop Range: mean {reactive_bid_prop_mean_range}, std {reactive_bid_prop_std_range}")
    print(f"Reactive Knowledge of Public Range: mean {reactive_others_mean_range}, std {reactive_others_std_range}")
    print(f"Cutoff Time Range: {cutoff_time_range}")
    print(f"Simulation Rounds: {num_rounds}")
    print("===================================\n")