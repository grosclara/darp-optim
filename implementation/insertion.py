# -*- coding: utf-8 -*-

from heapq import heappush, heappop
from logging import log, DEBUG
from math import inf

from data import sets, node_to_station, parameters, nb_bookings, bookings, shifts
from class_init import ShiftScheduleBlock, Insertion


############### INITIALIZATION ###############


def _initialize_shift_schedules(shifts):
    schedules = {}
    for shift in shifts :
        schedules[shift] = ShiftScheduleBlock(shift)
    return schedules


############### CONSTRAINTS ###############

def _check_capacity_constraint(schedule, booking, node_before_pick_up, node_before_drop_off):
        
    node = node_before_pick_up.next

    # If pick up and drop off are consecutive nodes
    if node_before_pick_up == node_before_drop_off :
        used_capacity = node["Used capacity"] + booking.passengers
        return used_capacity <= schedule.shift.capacity

    else :
        stop_to_drop_off = False
        while node != node_before_drop_off.next :
            used_capacity = node["Used capacity"] + booking.passengers
            if not used_capacity <= schedule.shift.capacity :
                return False

            node = node.next

    #Return also the new capacity
    return True


def _check_ride_time_constraint(schedule, deviation):
    #Déviation entre deux stations ???

    #Il faut séparer 3 types de shift
    #ceux où le drop off est avant--> aucun décalage
    #ceux où le pick up est avant et le drop off entre les deux > ride time + deviation pick-up
    #ceux où le pick up est après -> aucun décalage
    #pour calculer le ride time actuel on utilse AT_drop_off - AT_pick-up

    return True


def _check_turnover_constraint(schedule, booking):
    #Return also the new turnover
    return schedule.turnover + booking.price <= schedule.shift.max_turnover

def _check_insertion_feasibility_same_node(travel_time, node_before_pickup, schedule, booking):
    """cas particulier où node_before_pickup = node_befire_drop_off"""

    jobs_before = []
    jobs_after = []
    AT_before_pickup = node_before_pickup.value['Arrival time']


    #deviation_pickup = compute_deviation_pickup(travel_time, node_before_pickup, booking, schedule)
    #deviation_total = _compute_deviation(travel_time, node_before_pickup,node_before_drop_off, booking, schedule)

    for node in schedule.route :
        AT_node = node.value['Arrival time']
        if AT_node <= AT_before_pickup :
            jobs_before.append(node.value)
        else :
            jobs_after.append(node.value)

    time_route = AT_before_pickup + + node_before_pickup.value.duration

    time_route += travel_time[node_to_station[node_before_pickup.value.job_id], node_to_station[booking.jobs[0].job_id]]
    if time_route < booking.jobs[0].tw_start :
        time_route = booking.jobs[0].tw_start + booking.jobs[0].duration
    elif time_route > booking.jobs[0].tw_end :
        #on ne peut pas aller chercher la personne dans les contraintes horaires
        return False
    else :
        time_route += booking.jobs[0].duration

    time_route += travel_time[node_to_station[booking.jobs[0].job_id], node_to_station[node_before_pickup.value.job_id]]

    for k in range(len(jobs_after)) :
        if k == 0 :
            job_before = node_before_pickup.value
        else :
            job_before = jobs_after[k-1]
        job = jobs_after[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        if time_route < job.tw_start:
            time_route = job.tw_start + job.duration
        elif time_route > job.tw_end :
            return False
        else :
            time_route += job.duration

    return True

def _check_insertion_feasibility(travel_time, node_before_pickup, node_before_drop_off, schedule, booking):
    #cette fonction va resortir "AT du client à insérer
    #les clients impactés sont  ensemble des client privé (drop-off avant le pick-up à insérer)
    #on regarde les évènements de manière indépendant de si elle sont des drop-off ou des pick-up
    #3 cas :
    #évènement <= node_before_pickup  : pas de changement bookings_before
    #node_before_pickup< évènement <= node_before_drop_off : décalage de deviation pick-up bookings_between
    #node_before_drop_off < évènement : décalage pick-up + drop_off bookings_after

    #il ne faut pas oublier l'hypothèse ou la voiture était s'était arrêter à une station pour attendre un client -> on doit calculer le temps du nouvel
    #itinéraire sans partir de AT

    #on construit les listes des différents cas

    jobs_before = []
    jobs_between = []
    jobs_after = []
    AT_before_pickup = node_before_pickup.value['Arrival time']
    AT_before_drop_off = node_before_drop_off.value['Arrival time']

    #deviation_pickup = compute_deviation_pickup(travel_time, node_before_pickup, booking, schedule)
    #deviation_total = _compute_deviation(travel_time, node_before_pickup,node_before_drop_off, booking, schedule)

    for node in schedule.route :
        AT_node = node.value['Arrival time']
        if AT_node <= AT_before_pickup :
            jobs_before.append(node.value)
        elif AT_node <= AT_before_drop_off :
            jobs_between.append(node.value)
        else :
            jobs_after.append(node.value)

    time_route = AT_before_pickup + node_before_pickup.value.duration
    #on ajoute le délai pour aller à booking

    time_route += travel_time[node_to_station[node_before_pickup.value], node_to_station[booking.jobs[0].job_id]]
    if time_route < booking.jobs[0].tw_start :
        time_route = booking.jobs[0].tw_start + booking.jobs[0].duration
    elif time_route > booking.jobs[0].tw_end :
        #on ne peut pas aller chercher la personne dans les contraintes horaires
        return False
    else :
        time_route += booking.jobs[0].duration

    for k in range(len(jobs_between)) :
        if k == 0 :
            job_before = booking.jobs[0]
        else :
            job_before = jobs_between[k-1]
        job = jobs_between[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        if time_route < job.tw_start:
            time_route = job.tw_start + job.duration
        elif time_route > job.tw_end :
            return False
        else :
            time_route += job.duration

     #on doit maintenant s'assurer pour les job après le pick-up que c'est valide
    if node_before_pickup != node_before_drop_off :
        time_route += travel_time[node_to_station[node_before_drop_off.value.job_id], node_to_station[booking.jobs[1].job_id]]
        if time_route < booking.jobs[1].tw_start:
            time_route = booking.jobs[1].tw_start + booking.jobs[1].duration
        elif time_route > booking.jobs[1].tw_end:
            # on ne peut pas aller chercher la personne dans les contraintes horaires
            return False
        else:
            time_route += booking.jobs[1].duration
    else :
        time_route += travel_time[node_to_station[booking.jobs[1].job_id], node_before_drop_off.value.job_id] \
                      + booking.jobs[1].duration


    for k in range(len(jobs_after)) :
        if k == 0 :
            job_before = booking.jobs[1]
        else :
            job_before = jobs_after[k-1]
        job = jobs_between[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        if time_route < job.tw_start:
            time_route = job.tw_start + job.duration
        elif time_route > job.tw_end :
            return False
        else :
            time_route += job.duration
    return True

############### UTILS ###############

def _compute_deviation(travel_time, node_before_pickup, node_before_drop_off, booking, schedule):

    # Compute also execution duration time !!

    if node_before_drop_off == node_before_pickup :
        deviation = - travel_time[node_before_pickup.value, node_before_pickup.next.value] \
                    + travel_time[node_before_pickup.value, node_to_station[booking.jobs[0].job_id]]\
                    + travel_time[node_to_station[booking.jobs[0].job_id], node_to_station[booking.jobs[1].job_id]]\
                    + travel_time[node_to_station[booking.jobs[1].job_id], node_before_drop_off.next.value]\
            
    else :
        deviation_pick_up =  - travel_time[node_to_station[node_before_pickup.value], node_to_station[node_before_pickup.next.value]]\
                            + travel_time[node_to_station[node_before_pickup.value], node_to_station[booking.jobs[0].job_id]] \
                            + travel_time[node_to_station[booking.jobs[0].job_id]], node_to_station[node_before_pickup.next.value]]
        deviation_drop_off =  - travel_time[node_to_station[node_before_drop_off.value], node_to_station[node_before_drop_off.next.value]]\
                            + travel_time[node_to_station[node_before_drop_off.value], node_to_station[booking.jobs[1].job_id]] \
                            + travel_time[node_to_station[booking.jobs[1].job_id], node_to_station[node_before_drop_off.next.value]]
        deviation = deviation_pick_up + deviation_drop_off

    return deviation

def _new_potential_insertions(schedule, booking, travel_time):

    # Initialization of the pick up location
    node_before_pickup = schedule[1].route.first # first possible node before pick up == start warehouse
    while node_before_pickup != schedule[1].route.last: # last possible node before pick up == end warehouse (right before drop off node)

        # Initialisation of the drop off location 
        node_before_drop_off = node_before_pickup # first possible node before drop off == start warehouse (right after pick up node)
        while node_before_drop_off != schedule.route.last: # last possible node before pick up == end warehouse
            
            # Do not add infeasible insertions
            capacity_constraint_checked = _check_capacity_constraint(schedule, booking, node_before_pickup)
            turnover_constraint_checked = _check_turnover_constraint(schedule, booking)
            insertion_feasible = _check_insertion_feasibility(schedule, booking)
            ride_time_constraint_checked = _check_ride_time_constraint()
            
            if capacity_constraint_checked & turnover_constraint_checked & insertion_feasible & ride_time_constraint_checked :
                    # Compute the cost function
                    deviation = _compute_deviation(travel_time, node_before_pickup, node_before_drop_off, booking, schedule)  
                    # Add the potential insertions to the heap
                    insertion = Insertion(booking, node_before_pick_up, node_before_drop_off, deviation)
                    sorting_key = deviation
                    heappush( schedule[1].potential_insertions, (sorting_key, insertion) )

            else :
                if __debug__ :
                    log(DEBUG-2,("Rejecting this configuration"))

        # Update potential drop off node insertion
        node_before_drop_off = node_before_drop_off.next
    # Update potential pick up node insertion
    node_before_pickup = node_before_pickup.next


def _seems_valid_insertion(insertion, route_current_d, unrouted, D, d, C):  
    # The node has been already inserted somewhere
    if not insertion.customer in unrouted:
        if __debug__:
            log(DEBUG-3,"Customer n%d is already routed."%insertion.customer)
        return False
    
    # Something else has already been inserted here, ignore
    if insertion.after_node.next != insertion.before_node:
        if __debug__:
            log(DEBUG-3,"Chain n%d-n%d-n%d is no longer possible."%
                      (insertion.after_node.value, insertion.customer, insertion.before_node.value))
        return False
    
    # Also the available capacity may have changed,
    #  check if inserting would break a constraint
    if C:
        d_inc = d[insertion.customer]
        if route_current_d+d_inc-C_EPS>C:
            if __debug__:
                log(DEBUG-3,"Insertion of n%d would break C constraint."%insertion.customer)
            return False
    
    return True


def _try_insert_and_update(insertion, rd, D, L, minimize_K):
    if not minimize_K:
        # Compared to a solution where the customer is served individually
        insertion_cost = insertion.cost_delta\
                         -D[0,insertion.customer]\
                         -D[insertion.customer,0]
        if insertion_cost > 0:
            if __debug__:
                log(DEBUG-2,("Rejecting insertion of n%d "%insertion.customer)+
                            ("as it is expected make solution worse."))
            return False, None
        
    if L and rd.cost+insertion.cost_delta-S_EPS > L:
        return False, None
    else:
        inserted = rd.route.insert(insertion.customer, insertion.before_node)                
        rd.cost += insertion.cost_delta
        rd.used_capacity += insertion.demand_delta 
        new_edges = [ (insertion.after_node, inserted), (inserted, insertion.before_node) ]
        return True, new_edges


############### INSERTION HEURISTICS ###############


def insertion_init(parameters, bookings, shifts):

    # Generate the list of initial schedule for each shift (from warehouse to warehouse)
    schedules = _initialize_shift_schedules(shifts)
            
    # Build an ordered priority queue of potential bookings to initialize a route
    # Bookings are sorted according to their earliest pick up time windows
    seed_bookings = list(zip([booking.jobs[0].tw_start for booking in bookings], [booking.booking_id for booking in bookings]))
    seed_bookings.sort(reverse=True)

    # Process each booking 
    # While there are unprocessed bookings :
    while len(seed_bookings)>0 :

        booking_to_schedule = seed_bookings.pop()

        # Generate the potential insertions of booking_to_schedule for each shift
        for schedule in schedules.items() :
            _new_potential_insertions(schedule, booking_to_schedule, parameters["time_table_dict"], node_to_station)
            
        # Choose the most relevant shift with the lower cost function in which to insert booking_to_schedule
        opt_insertion, min_deviation = None, inf
        for schedules in schedules.items() :
            if len(schedule[1].potential_insertions) == 0: # Can't insert booking_to_schedule in this shift schedule
                continue
            else :
                # Unpack the best candidate from the insertion heap
                _, insertion = headpop(schedule[1].potential_insertions)
                if insertion.deviation < min_deviation:
                    min_deviation = insertion.deviation
                    opt_insertion = insertion

        if opt_insertion != None : # Check if the booking can be inserted somewhere

            if __debug__:
                log(DEBUG,"Chose to insert n%d resulting in route %s (%.2f)"%
                        (opt_insertion.booking, str(list(schedule.route)), schedule.cost))         

            # Insert the booking_to_schedule in the chosen schedule and update its characteristics
            _insert_and_update(schedule, opt_insertion)

            if insertion_successful :
                seed_bookings.remove(opt_insertion.booking) 
            else :           
                if __debug__:
                    log(DEBUG-2,"Problem while insert booking !!!")
                
        else : 
            if __debug__:
                log(DEBUG-2,"Booking rejected") 

                              
    return schedules



# ---------------------------------------------------------------------
def get_si_algorithm():
    algo_name = "Insertion heuristic"
    algo_desc = "Mole & Jameson (1976) sequential cheapest insertion heuristic "+\
                "without local search (van Breedam 1994, 2002)"
    def call_init(parameters, bookings, shifts):
        return insertion_init(parameters, bookings, shifts)
    
    return (algo_name, algo_desc, call_init)

if __name__=="__main__":
    get_si_algorithm()
