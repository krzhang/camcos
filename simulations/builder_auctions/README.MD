# Auction Simulator: Builder Strategies & User Guide

This repository contains a Python-based auction simulator modeling strategic bidding behavior under latency constraints. The simulator explores dynamics inspired by Stackelberg games and sealed-bid first-price auction (FPA) mechanisms, tailored toward block-building or builder-style auctions.

## Overview

Players are modeled as agents with different latency characteristics and strategic behaviors. Each player bids for blocks over multiple rounds, and their profits accumulate over time.

## Player Types

Defined in `player.py`, the simulator supports two types of players:

- **GaussianRangePlayer**
  - Acts as a *leader* in the Stackelberg framework.
  - Bids immediately based on a private bid proportion and latency.
  - Represents *slower* builders who must commit early due to higher latency (i.e., lower speed).

- **ReactiveGaussianRangePlayer**
  - Acts as a *follower* in the Stackelberg framework.
  - Observes available bids (within their latency window) and adjusts their bid accordingly.
  - Represents *faster* builders with low latency and adaptive bidding capabilities.

## Configuration

Settings are defined at the top of `main.py`. You can configure:

1. **Number of players** and how many are reactive.
2. **Speed (latency) ranges** for each type of player.
3. **Bid proportion parameters**, defining how aggressive players are in bidding.
4. **Cutoff time range** to simulate the time window for bid submissions.
5. **Simulation length** via `num_rounds`.

## Running the Simulation

Run `main.py` to:
- Generate players with randomized characteristics (within the specified parameter ranges).
- Simulate an auction over many rounds.
- Display detailed outputs including:
  - Each player's strategy, speed, and bidding behavior.
  - Final profits/winnings.
  - Sorted summary of all players ranked by their success.

### Optional: Display Settings

You can enable `print_settings = True` at the top of `main.py` to print all current configuration values before the simulation runs. This is useful for debugging or for verifying experimental setups.

## Customizing Strategy Logic

In `player.py`, the `ReactiveGaussianRangePlayer` class contains an `adjusted_bid` method. You can modify this logic to change how reactive players respond to observed bids. This is currently a heuristic and can be improved to simulate more realistic or competitive behaviors.

## File Structure

- `main.py`: Main simulation script. Set configurations and run experiments here.
- `auction.py`: Contains the `Auction` class which manages the auction rounds.
- `player.py`: Defines player strategies and bid logic.
- `player_setup.py`: Contains the `generate_players` function to create randomized player instances.
