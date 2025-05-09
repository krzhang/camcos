# Auction Simulator: Builder Strategies & User Guide

This repository contains a Python-based auction simulator modeling strategic bidding behavior under latency constraints. The simulator explores dynamics slightly inspired by Stackelberg games and sealed-bid first-price auction (FPA) mechanisms, tailored toward block-building or builder-style auctions.

## Overview

Players are modeled as agents with varying latency (submission delay) and bidding strategies. Each round, players submit bids for blocks, and profits are accumulated based on the difference between their private valuation and bid. The simulation runs for a configurable number of rounds.

## Player Types

Defined in `player.py`, the simulator supports two types of players:

- **GaussianRangePlayer**
  - Generally acts as a *leader* in the Stackelberg framework by submitting earlier.
  - Uses a Gaussian distribution to scale their private bid proportion and latency.
  - Represents *slower* builders who must commit early due to higher latency (lower speed).

- **ReactiveGaussianRangePlayer**
  - Generally acts as a *follower* in the Stackelberg framework by having the option to adapt their bid.
  - Observes available bids (within their latency window) and adjusts their bid accordingly based on estimates.
  - Represents *faster* builders with low latency and adaptive bidding capabilities.

## Configuration

Settings are defined at the top of `main.py`. You can configure:

1. **Number of players** and how many are reactive.
2. **Speed (latency) ranges** for each type of player.
3. **Bid proportion parameters**, defining how aggressive players are in bidding.
4. **Cutoff time range** to simulate the time window for bid submissions.
5. **Simulation length** via `num_rounds`.

Another setting that can be configured in 'player.py' is the "USE_UNIFORM_SAMPLING = True" at the top of the code.
When given True, all the distributions for bids and guesses will be sampled from uniform. When given False, sampled from gaussian distribution.


## Running the Simulation

Run `main.py` to:
- Generate players with randomized characteristics (within the specified parameter ranges).
- Simulate an auction over many rounds.
- Display detailed outputs including:
  - Each player's strategy, speed, and bidding behavior.
  - Final profits/winnings.
  - Sorted summary of all players ranked by their success.

### Optional: Display N Round(s)

You can enable `print_first_n_rounds = True` and set `n_rounds_to_print = #` at the top of `main.py` to print the round info for # rounds, displaying each player's final bids and submit times. This is useful for debugging or for verifying experimental setups.

### Optional: Display Settings

You can enable `print_settings = True` at the top of `main.py` to print all current configuration values before the simulation runs. This is useful for debugging or for verifying experimental setups.

## File Structure

- `main.py`: Main simulation script. Set configurations and run experiments here.
- `auction.py`: Contains the `Auction` class which manages the auction rounds.
- `player.py`: Defines player strategies and bid logic.
- `player_setup.py`: Contains the `generate_players` function to create randomized player instances.