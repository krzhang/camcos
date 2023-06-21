# CAMCOS Repository 

This is a repository of centralized CAMCOS stuff starting with Spring 2021. The current repository is a fork of [Mustafa's repo](https://github.com/mustafaqazi916/camcos).

## Links

- Google drive: https://drive.google.com/drive/folders/1xskDSaCgMP64lQnkxMnTWbHwFo4NnArI?usp=sharing

## A Comprehensive Guide to Running The Simulations

### 1. Transaction Data Scraper - *scrapers/scraper.py*
- Choose a start and end block number and enter it at line 45 and 46
- You can check the dates of the block given a block number with code from line 37 to 40
- Eg: Say you want a period of high demand. Block number 14170700 to 14177000 are transactions done on February 9, 2022 when the 2nd most expensive NFT was sold
- This should output csv files called "transactionData.csv" and "blockData.csv" under the /data directory.  
### 2. Transaction Modelling (Adam Aslam's code) - *simulations/notebooks/meip-1559_Joint_Distribution_Fitting.ipynb*
- This process takes in the scraped transaction data outputs an accurate transaction model for these 2 resources, ie gas and call data length
- Basically, what you would get is a csv file called specialGeneration.csv, which can be found under the directory /data. This file will be used later
- Make sure that line 20 "file=" is set to the file name you created in step 1. By default, it should be transactionData.csv
- You can tune the fitting parameter at ratioLimitGas at line 2 of the 3rd block. Recommended to be between 0.01 and 0.02
- **Note: When you generate the csv file, please add commas at Cov Lognormal Parameter for the last row. Refer to specialGenerationNFT.csv. I have yet to fix this bug**
### 3. Running Simulations
- Now we are finally ready to start simulating the Ethereum blockchain! There are many parameters that you can tune and choose from, the main ones are **resource, knapsack solver, and transaction decay time**
- We will go through what each parameter means and how to setup your simulator. For reference, all example code can be found under simulations/notebooks/example_test_cases.ipynb

**PART 1: The many parameters**

 **a. Choosing a resource package - *simulations/resources.py*** <br />
The first two resource methods were methods used by Spring 2022 and prior. Basically, a number is generated with
 pareto distribution with alpha 1.42150, beta 21000 (from empirical results) and split based on the ratio of resources.
For example, if you have 2 resources, gas and space with a ratio of 3:7 and generated a number of 2 from the pareto distribution,
gas would have an amount of 2* 0.3=0.6 and space would have 2* 0.7=1.4. You can think of it like Z=X+Y.
**Furthermore, the 4th method is the one you should be using, that uses the data from transaction modelling.**
<br />

i.  INDEPENDENT - Here, we generate one pareto value and split it with a random ratio such that both resources are uncorrelated </br>
ii. CORRELATED - Here, we generate one pareto value and split it with the given ratio. Eg, 30% gas and 70% call data


The following 2 resources are more like X+Y with no total limit but individual limits. This is likely the more accurate way for how transactions should be modelled

iii. INDIVIDUAL/MARGINAL - We generate 2 resources individually with no given ratio. They have individual basefees (ie: initial value, target and maximum limit, learning rate d) for each resource </br>
iv. JOINT - This is building upon Adam's code of generating transactions jointly. Namely, calldata and gas

 **b. Choosing a knapsack solver - *simulations/simulator.py*** <br />
You can find the implementation details of this under def def fill_block(self, time, method=None) in simulator.py

i. <ins>random</ins>: Transactions are randomly chosen until the block limit is reached
<br />
ii. <ins>greedy</ins>: Transactions are first sorted in the mempool based on tip amount and the transactions that 
generates largest profit will be prioritized and put into the block until the limit is reached. This approach is the current implementation from geth 
<br />
iii. <ins>backlog</ins>: Extending from the greedy approach, rejected transactions due to reaching the block limit are 
inserted into a min-heap. Transactions are popped from the min-heap when there is space
<br />
iv. <ins>dp (dynamic programming)</ins>: Finds the most optimized solution using a dynamic programming algorithm. A simple 
implementation exists for an 0-1 knapsack problem (2 dimensional resource) but scales in complexity with more resources. 
There also exists other knapsack solvers that are a mixture of greedy and dynamic that do not give the optimized solution but with smaller time complexity.
However, do note this implementation is currently **broken** since the space complexity is too large, there is another way 
of storing weights in the table instead which could solve this problem.
<br />

**b. Choosing a transaction decay - *simulations/simulator.py*** <br />
- Amount of time until a transaction is removed from the mempool
- We don’t want a randomly generated transaction to “clog” greedy block-filling algorithms permanently in the simulation.

**By default, we would be using JOINT resource package, GREEDY block-filling algorithm and NO transaction decay.** 

**PART 2: How do build a simution from scratch and tune various parameters**

For example code, look at **simulations/notebooks/example_test_cases.ipynb**. I will only be going through how to use JOINT 
resources here since that's the one we should be using

i. Setup basefee object for each resource, ie learning rate, target and maximum limit, initial value </br>
ii. Setup JointResource object that takes in the names of resources, basefees and the specialGeneration.csv you generated from step 2 </br>
iii. Setup demand object that sets initial number of transactions, time, number of transactions each turn and the resource object from the last step </br>
iv. Setup the simulator object by passing in your demand object and choose the relevant parameters for the knapsack 
solver (block-filling algorithm) and transaction decay. If you let these 2 parameters blank, the simulator will
use the default parameters aka "greedy" and no transaction decay </br>
v. Set the step count, aka how many blocks created in the blockchain </br>
vi. Simulate and it will output basefees_data, block_data, mempools_data, basefees_stats

### 4. Other files - running multiple iterations
Since taking one iteration of the simulation may not be truly representative, what I did was run the same simulation
8 times and averaged it. This was achieved by pushing my code onto a supercluster (a computer with multiple cores). 
This step may or may not be optional, but if you are interested, it is all under **simulations/shellscripts**

**a. run_simulator.sh** - This is a shellscript that runs each iteration (aka trajectory) 8 times (simultaneously on 8 cores) and then averages it.
Here you can see that we loop through the different learning rates and target limits for calldata. Reminder to change name 
of directory whenever you run this, if not the averaging will have problems. 

**b. single_trajectory_simulation.py** - Runs one iteration of the given parameters and saves the returned data as hdf5 and plots the individual figure

**c. average_trajectories.py** - Averages all the files of the given parameters in that directory and saves the averaged data as hdf5 and plots an individual figure

**d. plot_heatmap.py** - This code is used to plot a grid plot and heatmap for varying learning rates and 
target limit of calldata. The heatmap plots variance of basefees of calldata. Note that I first copied my files from 
the cluster to my local machine before plotting

**e. exploratory.py** - This is located within the scraper folder, please change the name of the CSV file to the dataset that you want to use, 
it will group the rows by CalldataUsage and filter them into random 5 transactions with some common CalldataUsage (0, 608, 64, 204).
You may change the output CSV of this file as well so you can not accidentally overwrite the other filtered dataset output.
