from insertion_v1 import drop_off, pick_up, time, station, clients, sorted_clients,insert_client, global_cost

from random import randint, random
from numpy import exp

# Formatting

def my_format_2_json(planning):
    nb_assigned_bookings=len(assigned_bookings(planning))
    shifts=[]
    route_cost = global_cost(planning)

    for shift in planning.keys():
        dic={}
        dic["id"] = shift
        jobs=[]
        for job in planning[shift]:
            jobs.append({"id":job[0],"time":job[1]})
        dic["jobs"]=jobs
        shifts.append(dic)

    resjson={"nb_assigned_bookings":nb_assigned_bookings,"route_cost":route_cost,"shifts":shifts}
    return resjson

def json_2_my_format(resjson):
    planning = {}
    for shift in resjson["shifts"]:
        schedule = []
        for job in shift["jobs"]:
            schedule.append([job["id"],job["time"]])
        planning[shift["id"]] = schedule
    return planning


# Inverse of the sum of the travel times for each booking
epsilon = 0
jobs = [job for job in drop_off.values()] + [job for job in pick_up.values()]
for job1 in jobs:
    for job2 in jobs:
        epsilon += time[(station[job1], station[job2])]
epsilon = 1/epsilon


def assigned_bookings(planning):
    """
        Returns the list of assigned bookings
    """
    res = []
    for emploi_du_temps in affectation.values():
        for k in range(1,len(emploi_du_temps)-1):
            if clients[emploi_du_temps[k][0]] not in res:
                res.append(clients[emploi_du_temps[k][0]])
    return(res)


def fluctuation(planning) :
    """
        Randomly take a customer from among all the customers and assign him a vehicle within the respect of constraints
    """

    # Choose the booking to be processed
    m = randint(0, nb_bookings-1)
    client = sorted_clients[m][1]

    shifts = [shift for shift in planning.keys()]
    index_shift = -1

    if client in assigned_bookings(planning) :
        stop = False
        for k in range(len(shifts)) :
            for i in range(1, len(planning[shifts[k]])-1) :
                if clients[planning[shifts[k]][i][0]] == client :

                    index_pick_up = i
                    index_shift = k
                    index_drop_off = None

                    for j in range(i+1, len(planning[shifts[k]])-1):
                        
                        if clients[planning[shifts[k]][j][0]] == client :
                            index_drop_off = j
                            break

                    stop = True
                    break

            if stop :
                break

        shift_insert = shifts.pop(index_shift)

    candidates = []
    for shift in shifts :

        candidate_shift_k = insert_client(client, shift, planning[shift])

        for candidat in candidate_shift_k:
            candidates.append([candidat,shift])

    if len(candidates) == 0 :
        return None

    else:
        planning_bis = {}
        for shift in shifts :
            liste = []
            for course in planning[shift]:
                liste.append(course[:])
            planning_bis[shift] = liste

        m = randint(0, len(candidates)-1)
        planning_bis[candidates[m][1]]=candidates[m][0]
        if index_shift >= 0 :
            liste=[]
            for course in planning[shift_insert]:
                liste.append(course[:])
            liste.pop(index_drop_off)
            liste.pop(index_pick_up)
            planning_bis[shift_insert] = liste

    return planning_bis


def energy(planning) :
    return(- (len(assigned_bookings(planning)) - epsilon*global_cost(planning)))


def simulated_annealing(planning, _T0, _lambda, iter_max) :
    """
        Applies the simulated annealing algorithm: returns True if it finds a better solution than the initial one, False if not.

    """

    def temperature(T):
        return(T * _lambda)

    # Initialization
    n = 0
    T = _T0
    E0 = energy(planning=initial_solution, unassigned_bookings=unassigned_clients)
    Emin = E0
    optimal_planning = initial_solution

    while n <= iter_max :
        new_solution = fluctuation(planning=optimal_planning)

        if new_solution != None :

            dif = energy(new_solution) - energy(optimal_planning)

            if dif <= 0 :
                optimal_planning = new_solution
                print("Energy loss")

            else:
                p = random()
                if p < exp(-dif/T):
                    optimal_planning = new_solution
                    print("Energy gain")

        T = temperature(T)
        n+=1
    
    E_min = energy(planning=optimal_planning, unassigned_bookings=optimal_unassigned_bookings)

    if Emin < E0:
        print("Better solution")
        nom="essai_T0="+str(_T0)+"_lambda="+str(_lambda)+"iter="+str(iter_max)
        nom=nom.replace('.',',')
        with open(nom+".json", 'w', encoding='utf-8') as f:
            json.dump(my_format_2_json(optimal_planning), f, indent=4)
        return True

        route_cost = json_writing(optimal_planning, file_name = 'heuristics/results/'+nom+'.json')
        return route_cost

    else:
        print("Any improvement")
        return None


################### PARAMETERS ###################
_T0 = 1.7*10**-6
_lambda = 0.95
iter_max = 500

if __name__ == '__main__' :

    with open("results/week2_data.json") as json_data:
    resjson = json.load(json_data)

    shift_schedules = json_2_my_format(resjson)

    simulated_annealing(initial_solution = shift_schedules, _T0 = _T0, _lambda = _lambda, iter_max=iter_max, sorted_clients=sorted_clients)

