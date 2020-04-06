from insertion import *

from random import randint, random
from numpy import exp


# Inverse of the sum of the travel times for each booking
epsilon = 0
jobs = [job for job in drop_off.values()] + [job for job in pick_up.values()]
for job1 in jobs:
    for job2 in jobs:
        epsilon += time[(station[job1], station[job2])]
epsilon = 1/epsilon


def fluctuation(planning, unassigned_bookings, sorted_clients) :
    """
        Randomly take a customer from among all the customers and assign him a vehicle within the respect of constraints
    """

    unassigned_bookings_bis = unassigned_bookings[:]

    # Choose the booking to be processed
    m = randint(0, nb_bookings-1)
    client = sorted_clients[m][1]

    shifts = [shift for shift in planning.keys()]
    index_shift = -1

    if client not in unassigned_bookings :
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

                    if index_drop_off == None :
                        print(planning[shift[k]])
                        print("Error")

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
        else:
            unassigned_bookings_bis.append(client)

    return planning_bis, unassigned_bookings_bis


def energy(planning, unassigned_bookings) :
    return(- (nb_bookings - len(unassigned_bookings) - epsilon*global_cost(planning)))


def simulated_annealing(initial_solution, unassigned_clients, _T0, _lambda, iter_max, sorted_clients) :
    """
        Applies the simulated annealing algorithm: returns True if it finds a better solution than the initial one, False if not.

    """

    def temperature(T, n):
        return(T * _lambda)

    # Initialization
    n = 0
    T = _T0
    E0 = energy(planning=initial_solution, unassigned_bookings=unassigned_clients)
    Emin = E0
    optimal_planning = initial_solution
    optimal_unassigned_bookings = unassigned_clients

    while n <= iter_max :
        new_solution = fluctuation(planning=optimal_planning, unassigned_bookings=optimal_unassigned_bookings, sorted_clients=sorted_clients)

        if new_solution != None :

            dif = energy(new_solution[0], new_solution[1]) - energy(optimal_planning,optimal_unassigned_bookings)

            if dif <= 0 :
                optimal_planning = new_solution[0]
                optimal_unassigned_bookings = new_solution[1]
                print("Energy loss")

            else:
                p = random()
                if p < exp(-dif/T):
                    optimal_planning = new_solution[0]
                    optimal_unassigned_bookings = new_solution[1]
                    print("Energy gain")

        T = temperature(T,n)
        n+=1
    
    E_final = energy(planning=optimal_planning, unassigned_bookings=optimal_unassigned_bookings)

    if E_final < E0:
        print("Better solution")
        nom="essai_T0="+str(_T0)+"_lambda="+str(_lambda)+"iter="+str(iter_max)
        nom=nom.replace('.',',')
        route_cost = json_writing(optimal_planning, optimal_unassigned_bookings, file_name = 'heuristics/results/'+nom+'.json')
        print(route_cost)
        return route_cost

    else:
        print("Any improvement")
        return None


################### PARAMETERS ###################
_T0 = 1.7*10**-6
_lambda = 0.95
iter_max = 500

if __name__ == '__main__' :
    shift_schedules , unassigned_clients, sorted_clients = init_insertion(sorted = True, file_name = "heuristics/results/test.json", save = False)
    simulated_annealing(initial_solution = shift_schedules, unassigned_clients = unassigned_clients, _T0 = _T0, _lambda = _lambda, iter_max=iter_max, sorted_clients=sorted_clients)

