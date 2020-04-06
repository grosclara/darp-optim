from simulated_annealing import *
from insertion import *
import numpy as np
import matplotlib.pyplot as plt

epsilon_bis = 1.1846608174512669e-08

T0_list = np.arange(5*10**-9,2.5*10**-6,5*10**-9)
#T0_list = [7.10**-7]
lambda_list = np.arange(0.01,0.99,0.01)
#lambda_list = [0.95]
iter_max = 500

xs = []
ys = []
tuning = []

for _T0 in T0_list :
    for _lambda in lambda_list :
        shift_schedules , unassigned_clients, sorted_clients = init_insertion(sorted = True, file_name = "heuristics/results/test.json", save = False)
        res = simulated_annealing(initial_solution = shift_schedules, unassigned_clients = unassigned_clients, _T0 = _T0, _lambda = _lambda, iter_max=iter_max, sorted_clients=sorted_clients)
        if res :
            xs.append(_T0)
            ys.append(_lambda)
            tuning.append(res)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.scatter(xs, ys, tuning)
ax.set_xlabel('Initial temperature (T0)')
ax.set_ylabel('Cooling rate (lambda)')
ax.set_zlabel('Route cost')

plt.show()  