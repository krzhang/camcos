import random
import player

def generate_players(
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
):
    players = []
    player_ids = list(range(num_players))
    random.shuffle(player_ids)  # Shuffle player IDs to randomize the order

    num_gaussian = num_players - num_reactive

    for _ in range(num_gaussian):
        p_id = player_ids.pop()
        # Speed range allocation
        speed_min = random.uniform(*gaussian_speed_min_range)   # Lower bounds
        speed_max = random.uniform(*gaussian_speed_max_range)   # Max bounds
        if speed_max < speed_min:
            speed_min, speed_max = speed_max, speed_min         # Ensure valid range

        # Bid proportion aggressiveness and variability allocation
        mean = random.uniform(*gaussian_bid_prop_mean_range)
        stddev = random.uniform(*gaussian_bid_prop_std_range)

        p = player.GaussianRangePlayer(p_id, (speed_min, speed_max), (mean, stddev))
        players.append(p)

    for _ in range(num_reactive):
        p_id = player_ids.pop()
        # Speed range allocation
        speed_min = random.uniform(*reactive_speed_min_range)   # Lower bounds
        speed_max = random.uniform(*reactive_speed_max_range)   # Max bounds
        if speed_max < speed_min:
            speed_min, speed_max = speed_max, speed_min         # Ensure valid range

        # Bid proportion aggressiveness and variability allocation
        mean = random.uniform(*reactive_bid_prop_mean_range)
        stddev = random.uniform(*reactive_bid_prop_std_range)
        # Knowledge of others' bid proportion, to attempt guessing
        others_mean = random.uniform(*reactive_others_mean_range)
        others_stddev = random.uniform(*reactive_others_std_range)

        p = player.ReactiveGaussianRangePlayer(
            p_id,
            (speed_min, speed_max),
            (mean, stddev),
            (others_mean, others_stddev)
        )
        players.append(p)

    random.shuffle(players)  # Shuffle the players list to randomize the order
    return players