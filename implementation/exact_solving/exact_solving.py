# Import of the pyomo module
import pyomo.environ as pyo
from pyomo.util.infeasible import log_infeasible_constraints
# from gurobipy import *
import csv

from extract_data import sets, node_to_station, parameters, nb_bookings

# Creation of an Abstract Model
model = pyo.AbstractModel()

# SETS
model.M = pyo.Set(initialize=sets["shift"], doc="Shifts")
model.P = pyo.Set(initialize=sets["pick_up"], doc="Pick up nodes")
model.D = pyo.Set(initialize=sets["drop_off"], doc="Drop off nodes")
model.PuD = pyo.Set(initialize=sets["pud"], doc="Pick up and drop off nodes")
model.V = pyo.Set(initialize=sets["node"], doc="Pick up, drop off and warehouses nodes")
model.S = pyo.Set(initialize=sets["station"], doc="Stations")

model.M.construct()
model.P.construct()
model.D.construct()
model.PuD.construct()
model.V.construct()
model.S.construct()


# PARAMETERS

model.t = pyo.Param(model.S, model.S, initialize=parameters["time_table_dict"], within=pyo.Any, doc='Time travel')
model.e = pyo.Param(model.V, initialize=parameters["duration_dict"], within=pyo.Any, doc="Run time")
model.tw = pyo.Param(model.V, initialize=parameters["tw_dict"], within=pyo.Any, doc="Booking time window")
model.m_max = pyo.Param(model.P, initialize=parameters["max_duration_dict"], within=pyo.Any, doc="Booking max duration")
model.q_req = pyo.Param(model.V, initialize=parameters["passengers_dict"], within=pyo.Any, doc="Passenger load shift")
model.r = pyo.Param(model.P, initialize=parameters["price_dict"], within=pyo.Any, doc="Booking price")
model.C = pyo.Param(model.M, initialize=parameters["capacity_dict"], within=pyo.Any, doc="Max capacity")
model.tw_driver = pyo.Param(model.M, initialize=parameters["tw_driver_dict"], within=pyo.Any, doc="Shift time window")
model.R = pyo.Param(model.M, initialize=parameters["max_turnover_dict"], within=pyo.Any, doc="Max driver turnover")

# VARIABLES

model.u = pyo.Var(model.V, model.M, within=pyo.NonNegativeReals, doc="Arrival time of a shift at a station")
model.q = pyo.Var(model.V, model.M, within=pyo.NonNegativeIntegers, doc="Shift load at a station")
model.x = pyo.Var(model.V, model.V, model.M, within=pyo.Boolean, doc='Path decision variable')  # Binary
model.m = pyo.Var(model.P, model.M, within=pyo.NonNegativeReals, doc="Booking duration")


# CONSTRAINTS

def c1_rule(model, i):
    return pyo.inequality(0, sum(model.x[i, j, k] for j in model.V for k in model.M), 1)


model.c1 = pyo.Constraint(model.P, rule=c1_rule, doc='Request satisfied at most once')


def c2_rule(model, i, k):
    return pyo.inequality(0, sum(model.x[i, j, k] for j in model.V) - sum(model.x[j, i, k] for j in model.V), 0)


model.c2 = pyo.Constraint(model.PuD, model.M, rule=c2_rule, doc='Graph constraint')


def c3_rule(model, k):
    return pyo.inequality(1, sum(model.x[0, j, k] for j in model.V), 1)  # for j in model.P


model.c3 = pyo.Constraint(model.M, rule=c3_rule, doc='Shift start constraint')


def c4_rule(model, k):
    return pyo.inequality(1, sum(model.x[i, 2 * nb_bookings + 1, k] for i in model.V), 1)


model.c4 = pyo.Constraint(model.M, rule=c4_rule, doc='Shift end constraint')


def c5_rule(model, i, k):
    return pyo.inequality(0,
                          sum(model.x[i, j, k] for j in model.V) - sum(model.x[nb_bookings + i, j, k] for j in model.V),
                          0)


model.c5 = pyo.Constraint(model.P, model.M, rule=c5_rule, doc='Request done by one vehicule')


def c6_rule(model, i, j, k):
    mij = model.e[i] + model.t[node_to_station[i], node_to_station[j]] + model.tw[i][1] - model.tw[j][0]
    Mij = max(0, mij)
    return model.u[j, k] >= model.u[i, k] + model.e[i] + model.t[node_to_station[i], node_to_station[j]] - Mij * (
                1 - model.x[i, j, k])


model.c6 = pyo.Constraint(model.V, model.V, model.M, rule=c6_rule, doc='Coherence visit time')


def c7_rule(model, i, k):
    return pyo.inequality(model.tw[i][0], model.u[i, k], model.tw[i][1])


model.c7 = pyo.Constraint(model.PuD, model.M, rule=c7_rule, doc='Client time window')


def c8_rule(model, i, k):
    return pyo.inequality(0, model.m[i, k] - model.u[nb_bookings + i, k] + (model.u[i, k] + model.e[i]), 0)


model.c8 = pyo.Constraint(model.P, model.M, rule=c8_rule, doc='Total request time')


def c9_rule(model, i, k):
    return pyo.inequality(model.t[node_to_station[i], node_to_station[nb_bookings + i]], model.m[i, k], model.m_max[i])


model.c9 = pyo.Constraint(model.P, model.M, rule=c9_rule, doc='Ride time limit')


def c10_rule(model, i, j, k):
    Qik = min(model.C[k], model.C[k] + model.q_req[i])
    return model.q[j, k] >= model.q[i, k] + model.q_req[j] - Qik * (1 - model.x[i, j, k])


model.c10 = pyo.Constraint(model.V, model.V, model.M, rule=c10_rule, doc='Coherence load vehicule')


def c11_rule(model, i, k):
    return pyo.inequality(max(0, model.q_req[i]), model.q[i, k], min(model.C[k], model.C[k] + model.q_req[i]))


model.c11 = pyo.Constraint(model.V, model.M, rule=c11_rule, doc='Vehicule capacity constraint')


def c12_rule(model, k):
    return model.u[0, k] >= model.tw_driver[k][0]


model.c12 = pyo.Constraint(model.M, rule=c12_rule, doc='Shift begin')


def c13_rule(model, k):
    return model.u[2 * nb_bookings + 1, k] <= model.tw_driver[k][1]


model.c13 = pyo.Constraint(model.M, rule=c13_rule, doc='Shift end')


def c14_rule(model, k):
    return pyo.inequality(0, sum(model.r[i] * model.x[i, j, k] for i in model.P for j in model.V), model.R[k])


model.c14 = pyo.Constraint(model.M, rule=c14_rule, doc='Driver turnover constraint')


def c15_rule(model):
    return pyo.inequality(0, sum(model.x[i, i, k] for i in model.V for k in model.M), 0)


model.c15 = pyo.Constraint(rule=c15_rule, doc='No loop constraint')

# DEFINE OBJECTIVE AND SOLVE

def objective_rule(model):
    # Epsilon should be greater than the total possible distance travelled by the whole vehicle fleet
    eps = 1/sum(model.t[i,j] for i in model.S for j in model.S)
    return sum(model.x[i, j, k] for i in model.P for j in model.V for k in model.M) - eps * sum(
        model.t[node_to_station[i], node_to_station[j]] * model.x[i, j, k] for i in model.V for j in model.V for k in
        model.M)


model.objective = pyo.Objective(rule=objective_rule, sense=pyo.maximize, doc='Objective function')


# Display of the output
def pyomo_postprocess(options=None, instance=None, results=None):
    # instance.pprint()
    instance.x.display()
    # instance.write()
    pass


if __name__ == '__main__' :
    instance = model.create_instance()
    opt = pyo.SolverFactory("gurobi")
    results = opt.solve(instance, tee=True)
    instance.solutions.load_from(results)
    print("\nDisplaying Solution\n" + '-' * 60)
    print(log_infeasible_constraints(model))
    pyomo_postprocess(None, instance, results)
