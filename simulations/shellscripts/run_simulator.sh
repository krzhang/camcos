#!/bin/bash

#SBATCH -o /home/yteoh/results/slurm-%j.out # STDOUT
#SBATCH --nodes=8
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=yikhaw.teoh@sjsu.edu

module purge
module load intel-python3 openmpi-3.0.1/intel intel
source activate p310
export PYTHONPATH=/home/yteoh/camcos/

call_data_standard_value=25
call_data_learning_rate=1/8
call_data_target_limit=25000
step_count=400
directory="final_result"
filename="specialGeneration.csv"

call_data_learning_rates=("1/13" "1/11" "1/8" "3/8" "5/8")
#call_data_standard_values=("25")
call_data_target_limits=("60000" "72500" "75000" "77500" "90000")

for i in "${call_data_learning_rates[@]}"
do
  for j in "${call_data_target_limits[@]}"
  do
  srun --ntasks 8 python /home/yteoh/camcos/simulations/shellscripts/single_trajectory_simulation.py $call_data_standard_value "$i" "$j" $step_count $directory $filename
  srun --ntasks 1 python /home/yteoh/camcos/simulations/shellscripts/average_trajectories.py $call_data_standard_value "$i" "$j" $step_count $directory
  done
done