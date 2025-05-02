import player
from main import Auction
from formatting import FormatPrinter
import random

# Assign number of players in auction
num_players = 10

# Assign number of gaussian and reactive gaussian players
num_gaussian = 5
num_reactive = 5

# Initiliaze players array
players = []

# Assign unique player IDs from 0 to 9 to an array
player_ids = list(range(num_players))
# Shuffle players to randomize player's strategy
random.shuffle(player_ids)

# First assign Gaussian players
for _ in range(num_gaussian):
    p_id = player_ids.pop()

    # Own speed
    speed_min = random.uniform(0.0, 0.2)  # Example lower bounds
    speed_max = speed_min + random.uniform(0.2, 0.4)  # Always ensure valid range

    # Own bid_prop mean and variance
    mean = random.uniform(0.75, 0.95)  # bid proportion aggressiveness
    stddev = random.uniform(0.3, 0.5)  # Player variability on bid proportion

    p = player.GaussianRangePlayer(p_id, (speed_min, speed_max), (mean, stddev))
    players.append(p)

    print(f"Player {p_id}: Gaussian, speed=({speed_min:.2f},{speed_max:.2f}), mean={mean:.3f}, stddev={stddev:.3f}")


# Then assign Reactive Gaussian players
for _ in range(num_reactive):
    p_id = player_ids.pop()

    # Own speed
    speed_min = random.uniform(0.3, 0.5)
    speed_max = speed_min + random.uniform(0.3, 0.4)

    # Own bid_prop mean and variance
    mean = random.uniform(0.85, 0.95)
    stddev = random.uniform(0.2, 0.4)

    # Assumed others' bid_prop mean and variance for guessing
    others_mean = random.uniform(0.75, 0.95)
    others_stddev = random.uniform(0.3, 0.5)

    p = player.ReactiveGaussianRangePlayer(p_id, (speed_min, speed_max), (mean, stddev), (others_mean, others_stddev))
    players.append(p)

    print(f"Player {p_id}: Reactive, speed=({speed_min:.2f},{speed_max:.2f}), mean={mean:.3f}, stddev={stddev:.3f}, others_mean={others_mean:.3f}, others_stddev={others_stddev:.3f}")


auction = Auction(players)
round_results, winnings = auction.run_simulation(100000)

# Print winnings per player
for p_id, win in enumerate(winnings):
    print(f"Player {p_id} winnings: {win}")
