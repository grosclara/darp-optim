# -*- coding: utf-8 -*-

from heapq import heappush, heappop
from logging import log, DEBUG
from math import inf
from operator import itemgetter

from data import sets, node_to_station, parameters, nb_bookings, bookings, shifts
from class_init import ShiftScheduleBlock, Insertion


############### INITIALIZATION ###############

def _initialize_shift_schedules(shifts):
    schedules = []
    for shift in shifts :
        schedules.append(ShiftScheduleBlock(shift))
    return schedules


############### CONSTRAINTS ###############

def _check_capacity_constraint(schedule, booking, node_before_pick_up, node_before_drop_off):
        
    # If pick up and drop off are consecutive nodes
    if node_before_pick_up == node_before_drop_off :
        used_capacity = node_before_pick_up.value["Used capacity"] + booking.passengers
        return used_capacity <= schedule.shift.capacity

    # If pick up and drop off node are separated by at least one station
    else :
        # Check shift capacity between pick up and drop off nodes
        node = node_before_pick_up # Initialize checking at node before pick up
        while node != node_before_drop_off : # Terminate checking at node before drop off
            used_capacity = node.value["Used capacity"] + booking.passengers
            if not used_capacity <= schedule.shift.capacity :
                return False
            node = node.next

    return True


def _check_turnover_constraint(schedule, booking):

    return schedule.turnover + booking.price <= schedule.shift.max_turnover

def _check_ride_time_constraint():
#def _check_ride_time_constraint(schedule, deviation):
    #Déviation entre deux stations ???

    #Il faut séparer 3 types de shift
    #ceux où le drop off est avant--> aucun décalage
    #ceux où le pick up est avant et le drop off entre les deux > ride time + deviation pick-up
    #ceux où le pick up est après -> aucun décalage
    #pour calculer le ride time actuel on utilse AT_drop_off - AT_pick-up

    return True

def _check_insertion_feasibility(schedule, booking, node_before_pick_up, node_before_drop_off, deviation):



    EPT,LPT = booking.jobs[0].tw_start, booking.job[0].tw_end # pick up
    EDT, LDT = booking.jobs[1].tw_start, booking.job[1].tw_end # drop off

def _check_insertion_feasibility(travel_time, node_before_pickup, node_before_drop_off, schedule, booking):
    """
    :param travel_time: tableau indexé sur les numéros des stations
    :param node_before_pickup: de type node avec node.value de type {"Job":BookingJob,"Used capacity": int , "Arrival time": int, "Departure time": int}
    :param node_before_drop_off: de type node,
    :param schedule: liste de dictionnaire [ ... {"Job":BookingJob,"Used capacity": int , "Arrival time": int, "Departure time": int} ...]
    :param booking: de type Booking, (c'est le booking qu'on veut insérer  { ... "booking_job.id" : int ...}),

    :return: bool
    """
    #cette fonction va ressortir "AT du client à insérer
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
    AT_results ={}

    for node in schedule.route :
        AT_node = node.value['Arrival time']
        if AT_node <= AT_before_pickup :
            jobs_before.append(node.value)
            AT_results[node.value['Job'].job_id] = node.value["Arrival time"]
        elif AT_node <= AT_before_drop_off :
            jobs_between.append(node.value)
        else :
            jobs_after.append(node.value)

    time_route = AT_before_pickup + node_before_pickup.value.duration
    #on ajoute le délai pour aller à booking

    time_route += travel_time[node_to_station[node_before_pickup.value], node_to_station[booking.jobs[0].job_id]]
    if time_route < booking.jobs[0].tw_start :
        time_route = booking.jobs[0].tw_start
    elif time_route > booking.jobs[0].tw_end :
        #on ne peut pas aller chercher la personne dans les contraintes horaires
        return False, None

    AT_results[booking.jobs[0].job_id] = time_route
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
            return False, None
        AT_results[job.job_id] = time_route
        time_route += job.duration

     #on doit maintenant s'assurer pour les job après le pick-up que c'est valide

    time_route += travel_time[node_to_station[node_before_drop_off.value.job_id], node_to_station[booking.jobs[1].job_id]]
    if time_route < booking.jobs[1].tw_start:
        time_route = booking.jobs[1].tw_start
    elif time_route > booking.jobs[1].tw_end:
        # on ne peut pas aller chercher la personne dans les contraintes horaires
        return False, None

    AT_results[booking.jobs[1].job_id] = time_route
    time_route += booking.jobs[1].duration

    for k in range(len(jobs_after)) :
        if k == 0 :
            job_before = booking.jobs[1]
        else :
            job_before = jobs_after[k-1]
        job = jobs_between[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        if time_route < job.tw_start:
            time_route = job.tw_start
        elif time_route > job.tw_end :
            return False
        AT_results[job.job_id] = time_route
        time_route += job.duration
    return True, AT_results


############### UTILS ###############

def _compute_deviation(travel_time, node_before_pickup, node_before_drop_off, booking, schedule):

    # Compute also execution duration time !!

    if node_before_drop_off == node_before_pickup :
        deviation = - travel_time[node_before_pickup.value["Job"].station, node_before_pickup.next.value["Job"].station] \
                    + travel_time[node_before_pickup.value["Job"].station, booking.jobs[0].station]\
                    + travel_time[booking.jobs[0].station, booking.jobs[1].station]\
                    + travel_time[booking.jobs[1].station, node_before_drop_off.next.value["Job"].station]
            
    else :
        deviation_pick_up =  - travel_time[node_to_station[node_before_pickup.value], node_to_station[node_before_pickup.next.value]]\
                            + travel_time[node_to_station[node_before_pickup.value], node_to_station[booking.jobs[0].job_id]] \
                            + travel_time[node_to_station[booking.jobs[0].job_id]], node_to_station[node_before_pickup.next.value]
        deviation_drop_off =  - travel_time[node_to_station[node_before_drop_off.value], node_to_station[node_before_drop_off.next.value]]\
                            + travel_time[node_to_station[node_before_drop_off.value], node_to_station[booking.jobs[1].job_id]] \
                            + travel_time[node_to_station[booking.jobs[1].job_id], node_to_station[node_before_drop_off.next.value]]
        deviation = deviation_pick_up + deviation_drop_off

    return deviation


def _new_potential_insertions(schedule, booking, travel_time, node_to_station):

    # Initialization of the pick up location
    node_before_pick_up = schedule.route.first # first possible node before pick up == start warehouse
    while node_before_pick_up != schedule.route.last: # last possible node before pick up == end warehouse (right before drop off node)

        # Initialization of the drop off location 
        node_before_drop_off = node_before_pick_up # first possible node before drop off == start warehouse (right after pick up node)
        while node_before_drop_off != schedule.route.last: # last possible node before pick up == end warehouse
            
            # Do not add infeasible insertions
            capacity_constraint_checked = _check_capacity_constraint(schedule = schedule, 
                                                                    booking = booking, 
                                                                    node_before_pick_up = node_before_pick_up, 
                                                                    node_before_drop_off = node_before_drop_off)
            turnover_constraint_checked = _check_turnover_constraint(schedule, booking)
            insertion_feasible = _check_insertion_feasibility()
            ride_time_constraint_checked = _check_ride_time_constraint()
            
            if capacity_constraint_checked & turnover_constraint_checked & insertion_feasible & ride_time_constraint_checked :
                    # Compute the cost function
                    deviation = _compute_deviation(travel_time, node_before_pick_up, node_before_drop_off, booking, schedule)  
                    # Add the potential insertions to the heap
                    insertion = Insertion(booking, node_before_pick_up, node_before_drop_off, deviation)
                    sorting_key = deviation
                    heappush( schedule.potential_insertions, (sorting_key, insertion) )

            else :
                if __debug__ :
                    log(DEBUG-2,("Rejecting this configuration"))

            # Update potential drop off node insertion
            node_before_drop_off = node_before_drop_off.next
        # Update potential pick up node insertion
        node_before_pick_up = node_before_pick_up.next



def _update_capacity(schedule, insertion) :
    pick_up_node = insertion.node_before_pick_up.next
    drop_off_node = insertion.node_before_drop_off.next
    node = pick_up_node

    while node != drop_off_node : # Before the drop off node, increment the used capacity of each node
        node["Used capacity"] += insertion.booking.passengers
        node = node.next

def _update_turnover(schedule, insertion) :
    schedule.turnover += insertion.booking.passengers

def _update_schedule_timing(schedule, insertion):
    pass

def _insert_and_update(schedule, insertion):

    # Construct pick up and drop off nodes
    pick_up_node = 1 # Capacity of pick_up node == capacity of node_before_pick_up
    drop_off_node = 2 # Capacity of drop_off_node == capacity of node_before_drop_off

    # Insert pick up and drop off nodes
    schedule.route.insert(drop_off_node, node_before_drop_off.next)
    schedule.route.insert(pick_up_node, node_before_pick_up.next)

    # Updates

    # Turnover
    _update_turnover(schedule = schedule, insertion = insertion)
    # Capacity
    _update_capacity(schedule = schedule, insertion = insertion)
    # Schedule timing
    _update_schedule_timing(schedule = schedule, insertion = insertion)


############### INSERTION HEURISTICS ###############


def insertion_init(parameters = parameters, bookings = bookings, shifts = shifts, node_to_station = node_to_station):

    # Generate the list of initial schedule for each shift (from warehouse to warehouse)
    schedules = _initialize_shift_schedules(shifts = shifts)
            
    # Build an ordered priority queue of potential bookings to initialize a route
    # Bookings are sorted according to their earliest pick up time windows
    seed_bookings = list(zip([booking.jobs[0].tw_start for booking in bookings], [booking for booking in bookings]))
    seed_bookings = [sorted(seed_bookings,key=itemgetter(0), reverse=True)[k][1] for k in range(len(seed_bookings))]

    # Process each booking 
    # While there are unprocessed bookings :
    while len(seed_bookings)>0 :

        booking_to_schedule = seed_bookings.pop()

        # Generate the potential insertions of booking_to_schedule for each shift
        for schedule in schedules :
            _new_potential_insertions(schedule = schedule, 
                                    booking = booking_to_schedule, 
                                    travel_time = parameters["time_table_dict"], 
                                    node_to_station = node_to_station)
            
        # Choose the most relevant shift with the lower cost function in which to insert booking_to_schedule
        opt_insertion, min_deviation = None, inf
        for schedule in schedules :
            if len(schedule.potential_insertions) == 0: # Can't insert booking_to_schedule in this shift schedule
                continue
            else :
                # Unpack the best candidate from the insertion heap
                _, insertion = heappop(schedule.potential_insertions)
                if insertion.deviation < min_deviation:
                    min_deviation = insertion.deviation
                    opt_insertion = insertion

        if opt_insertion != None : # Check if the booking can be inserted somewhere

            if __debug__:
                log(DEBUG,"Chose to insert")      

            # Insert the booking_to_schedule in the chosen schedule and update its characteristics
            _insert_and_update(schedule = schedule, insertion = opt_insertion)

            if insertion_successful :
                seed_bookings.remove(opt_insertion.booking) 
            else :           
                if __debug__:
                    log(DEBUG-2,"Problem while insert booking !!!")
                
        else : 
            if __debug__:
                log(DEBUG-2,"Booking rejected") 

    print(schedules)
    return(schedules)                         



# ---------------------------------------------------------------------
def get_si_algorithm():
    algo_name = "Insertion heuristic"
    algo_desc = "Mole & Jameson (1976) sequential cheapest insertion heuristic "+\
                "without local search (van Breedam 1994, 2002)"
    return (algo_name, algo_desc, insertion_init(parameters, bookings, shifts, node_to_station))
    
if __name__=="__main__":
    get_si_algorithm()
    pass