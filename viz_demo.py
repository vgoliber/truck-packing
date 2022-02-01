# Copyright 2022 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.

from dimod import ConstrainedQuadraticModel, Binaries, quicksum 
from dwave.system import LeapHybridCQMSampler 
import random 
import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title('Packing a Truck to Maximize Value')

# Problem set up
num_packages = st.slider('Number of packages available:', 0, 500, 300)  # min: 0, max: 500, default: 300
# num_packages = 300

# Priority of each package, 3 = high priority, 1 = low priority
priority = random.choices((1, 2, 3), k=num_packages)

# Number of days since each package was ordered (More days need to be
# prioritized higher)
days_since_order = random.choices((0, 1, 2, 3), k=num_packages)

# Weight of each package
weight = random.choices(range(1, 101), k=num_packages)

# Maximum weight and number of packages the truck can handle
max_weight = 3000  
max_packages = 100

# Weights for the objective functions
obj_weight_priority = 1.0 
obj_weight_days = 1.0

imageLocation = st.empty()

# Characterize the problem
df = pd.DataFrame({'Priority': priority, 'Age': days_since_order, 'Weight': weight}, index=None)
problem_array = np.zeros((3, 4)).astype(int) 
for i in range(num_packages):
    problem_array[-1 * (priority[i]-3)][-1 * (days_since_order[i] - 3)] += 1

if st.checkbox('Show input data'):
    st.subheader('Input data')
    st.dataframe(df)

# Draw data distribution
# st.subheader('Package Data Distribution')
fig, ax = plt.subplots(1,3, constrained_layout=True, figsize=(8,8))
p1 = ax[0].hist(df['Priority'], bins=[0.5,1.5,2.5,3.5], histtype='bar',  rwidth=0.75, stacked=True)
ax[0].set_title('Priority')
p2 = ax[1].hist(df['Age'], bins=[-0.5,0.5,1.5,2.5,3.5], histtype='bar',  rwidth=0.8, stacked=True)
ax[1].set_title('Age')
p3 = ax[2].hist(df['Weight'], bins=10, histtype='bar',  rwidth=0.95, stacked=True)
ax[2].set_title('Weight')
plt.show()
imageLocation.pyplot()

build_load_state = st.text('Building CQM...')

# Build the CQM
cqm = ConstrainedQuadraticModel()

# Create the binary variables
bin_variables = list(Binaries(range(num_packages)))

# ----------------- Objective functions ----------------- 

# 1. Maximize priority shipping packages
objective1 = -obj_weight_priority * quicksum(priority[i] * bin_variables[i] 
                for i in range(num_packages))

# 2. Minimize customers wait time
objective2 = -obj_weight_days * quicksum(days_since_order[i] * bin_variables[i]
                for i in range(num_packages))

# Add the objectives to the CQM
cqm.set_objective(objective1 + objective2)

# ----------------- Constraints ----------------- 

# Add the maximum capacity constraint
cqm.add_constraint(quicksum(weight[i] * bin_variables[i] for i in
range(num_packages)) <= max_weight, label='max_weight')

# Add the maximum package (or truck size) constraint
cqm.add_constraint(quicksum(bin_variables[i] for i in range(num_packages)) 
                    == max_packages, label='max_packages')

build_load_state.text("Building CQM...Done!")

# -----------------  Submit to the CQM sampler -----------------
run_state = st.text('Sending to CQM hybrid solver...')
cqm_sampler = LeapHybridCQMSampler() 
sampleset = cqm_sampler.sample_cqm(cqm, label='Truck Packing Demo')
run_state.text("Sending to CQM hybrid solver...Done!")

# ----------------- Process the results -----------------
feasible_sampleset = sampleset.filter(lambda d: d.is_feasible)

if not len(feasible_sampleset): 
    st.write("\nNo feasible solution found.\n")

else: 
    first_feasible_sol = feasible_sampleset.first.sample

    # Calculate number of packages with each priority and number of days since
    # order in the solution
    
    df['Shipped'] = [first_feasible_sol[i] for i in range(len(first_feasible_sol))]
    # st.dataframe(df)

    mask = np.array(df['Shipped'], dtype=bool)
    priority_s, priority_ns = df['Priority'][mask], df['Priority'][~mask]
    age_s, age_ns = df['Age'][mask], df['Age'][~mask]
    weight_s, weight_ns = df['Weight'][mask], df['Weight'][~mask]

    chosen = [i for i in first_feasible_sol if first_feasible_sol[i] == 1]
    total_weight = quicksum(weight[i] for i in chosen) 

    # Characterize the solution 
    # Packages with higher priority (upper row) and the most days since the
    # order (left most column) should be prioritized in the selection

    # Draw data distribution
    st.subheader('Solution:')
    out_df = pd.DataFrame({'Shipped':[total_weight, len(chosen)], 'Limit':[max_weight, max_packages]}, index=['Weight', 'Num Packages'])
    st.table(out_df)
    fig, ax = plt.subplots(1,3, constrained_layout=True, figsize=(8,8))
    p1 = ax[0].hist([priority_s, priority_ns], bins=[0.5,1.5,2.5,3.5], histtype='bar',  rwidth=0.75, stacked=True)
    ax[0].set_title('Priority')
    p2 = ax[1].hist([age_s, age_ns], bins=[-0.5,0.5,1.5,2.5,3.5], histtype='bar',  rwidth=0.8, stacked=True)
    ax[1].set_title('Age')
    p3 = ax[2].hist([weight_s, weight_ns], bins=10, histtype='bar',  rwidth=0.95, stacked=True)
    ax[2].set_title('Weight')
    fig.legend([p1, p2, p3], labels = ["Shipped", "Not Shipped"], loc='upper left', borderaxespad=0.1,title="Legend")
    plt.show()
    imageLocation.pyplot()
