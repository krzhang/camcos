# Model Explanation and User Guide

This repository contains a Python-based auction simulator to model bidding dynamics of bidders.

The simulator models some of the Stackelberg game aspect combined with candlestick (candle) auctions and sealed-bid first-price auction (FPA) mechanisms.

## Player Types
Implemented in player.py, the simulator currently supports two types of players:

- GaussianRangePlayer
    - Leaders in the Stackelberg framework.
        - Each round, they bid immediately based on their private valuation of the block and their predefined latency(speed).

        - Models the behavior of “slow” builders who must commit to bids early due to their high latency(low speed).

- ReactiveGaussianRangePlayer
    - Followers in the Stackelberg framework.

        - These players observe bids submitted just before their own bid submission time (if any) and adjust their bid accordingly.

        - Models the behavior of “fast” builders capable of adaptive bidding strategies because of their low latency(high speed).

## Parameter Calibration

### Simulation_1 file
1. Assign number of players for the auction
2. Then assign number of players for each strategy
3. Adjust boundaries for self speed and self aggresivenss of bid proportion for both players
and guess proportion of reactive player
4. Adjust simulation rounds

Steps 3 & 4 can be adjusted for different bidding characteristics

Finally, run the code

### Player file
In the the ReactiveGaussianRangePlayer, you can change the adjusted_bid of how they would react upon seeing other bids. For now, this is arbritary
and can be subject to change. 

