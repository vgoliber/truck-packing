# Copyright 2021 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dimod import ConstrainedQuadraticModel, Binary, quicksum
from dwave.system import LeapHybridCQMSampler
import random
import numpy as np

# Problem set up
num_packages = 300

# Priority of each package, 3 = high priority, 1 = low priority
priority = [random.choice([1,2,3]) for i in range(num_packages)]

# Number of days since each package was ordered (More days need to be prioritized higher)
days_since_order = [random.choice([0,1,2,3]) for i in range(num_packages)]

# Weight of each package
weight = [random.randint(1, 100) for i in range(num_packages)]

# Maximum weight and number of packages the truck can handle
max_weight = 3000  
max_packages = 100

# Weights for the objective functions
obj_weight_priority = 1.0
obj_weight_days = 1.0

# Build the CQM
cqm = ConstrainedQuadraticModel()

# Create the binary variables
bin_variables = [Binary(i) for i in range(num_packages)]

# ----------------- Objective functions -----------------
# 1. Maximize priority shipping packages
objective1 = -obj_weight_priority * quicksum(priority[i] * bin_variables[i] for i in range(num_packages))

# 2. Minimize customers wait time
objective2 = -obj_weight_days * quicksum(days_since_order[i] * bin_variables[i] for i in range(num_packages))

# Add the objectives to the CQM
cqm.set_objective(objective1 + objective2)

# ----------------- Constraints -----------------
# Add the maximum capacity constraint
cqm.add_constraint(quicksum(weight[i] * bin_variables[i] for i in range(num_packages)) <= max_weight,
                   label='max_weight')

# Add the maximum package (or truck size) constraint
cqm.add_constraint(quicksum(bin_variables[i] for i in range(num_packages)) == max_packages,
                   label='max_packages')

# -----------------  Submit to the CQM sampler -----------------
cqm_sampler = LeapHybridCQMSampler()
sampleset = cqm_sampler.sample_cqm(cqm, label='Truck Packing Demo')

# ----------------- Process the results -----------------
feasible_sols = np.where(sampleset.record.is_feasible == True)

if len(feasible_sols[0]):
    first_feasible_sol = np.where(sampleset.record[feasible_sols[0][0]][0] == 1)

    # Characterize the problem
    problem_array = np.zeros((3, 4)).astype(int)
    for i in range(num_packages):
        problem_array[-1 * (priority[i]-3)][-1 * (days_since_order[i] - 3)] += 1

    print("\n****************** PROBLEM ******************\n")
    print('            Days since order was placed')
    print('{:>5s}{:>5s}{:>5s}{:>5s}{:>5s}'.format('Priority |', '3', '2', '1', '0'))
    print('-' * 40)

    for i in range(3):
        print('{:>5s}{:>10s}{:>5s}{:>5s}{:>5s}'.format(str(-1*(i - 3)), str(problem_array[i][0]), str(problem_array[i][1]),
                                                       str(problem_array[i][2]), str(problem_array[i][3])))

    # Calculate number of packages with each priority and number of days since order in the solution
    total_weight = quicksum(weight[i] for i in first_feasible_sol[0])
    solution_priorities = [priority[i] for i in first_feasible_sol[0]]
    solution_days_since_order = [days_since_order[i] for i in first_feasible_sol[0]]

    # Characterize the solution
    #   Packages with higher priority (upper row) and the most days since the order (left most column) should be
    #   prioritized in the selection
    results_array = np.zeros((3, 4)).astype(int)
    for i in first_feasible_sol[0]:
        results_array[-1 * (priority[i]-3)][-1 * (days_since_order[i] - 3)] += 1

    print("\n****************** SOLUTION ****************** ")
    print('            Days since order was placed')
    print('{:>5s}{:>5s}{:^5s}{:^5s}{:^5s}'.format('Priority |', '3', '2', '1', '0'))
    print('-' * 40)

    for i in range(3):
        print('{:>5s}{:>10s}{:^5s}{:^5s}{:^5s}'.format(str(-1*(i - 3)), str(results_array[i][0]), str(results_array[i][1]),
                                                       str(results_array[i][2]), str(results_array[i][3])))

    print(("\nTotal number of selected items: {}".format(len(first_feasible_sol[0]))))
    print("Total weight of selected items: {}".format(total_weight))
else:
    print("No feasible solutions found")

