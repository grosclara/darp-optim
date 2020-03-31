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

def _check_insertion_feasibility():
    return True

def _check_insertion_feasibility_same_node():
    return True 

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
    node_before_pickup = node_before_pickup.next


def _insert_and_update(insertion, opt_insertion):


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
                _, insertion = headpop(schedule.potential_insertions)
                if insertion.deviation < min_deviation:
                    min_deviation = insertion.deviation
                    opt_insertion = insertion

        if opt_insertion != None : # Check if the booking can be inserted somewhere

            if __debug__:
                log(DEBUG,"Chose to insert n%d resulting in route %s (%.2f)"%
                        (opt_insertion.booking, str(list(schedule.route)), schedule.cost))         

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

    return(schedules)                         
    print(schedules)



# ---------------------------------------------------------------------
def get_si_algorithm():
    algo_name = "Insertion heuristic"
    algo_desc = "Mole & Jameson (1976) sequential cheapest insertion heuristic "+\
                "without local search (van Breedam 1994, 2002)"
    return (algo_name, algo_desc, insertion_init(parameters, bookings, shifts, node_to_station))
    
if __name__=="__main__":
    get_si_algorithm()
