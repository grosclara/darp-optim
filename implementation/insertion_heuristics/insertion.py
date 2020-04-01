# -*- coding: utf-8 -*-

from heapq import heappush, heappop
from logging import log, DEBUG
from math import inf
from operator import itemgetter

from data import sets, node_to_station, parameters, nb_bookings, bookings, shifts
from class_init import ShiftScheduleBlock, Insertion


def _new_potential_insertions(shift, booking):
    _add_into_same_block(shift = shift, booking = booking)
    _add_into_different_blocks(shift = shift, booking = booking) # Merge blocks

def _add_into_same_block(shift, booking):
    """
        Trying to fit the booking into the existing working schedule while
        pickup and delivery happen in the same block
    """
    # shift.feasibleSchedules = []

    if shift.currentSchedules == [] :
        # case0 : first work block is being created if possible
        _case0(shift = shift, booking = booking)
    else :
        # Case1 : pickup and delivery are inserted at the end of the working schedule.
        _case1(shift = shift, booking = booking)        
        # Case 2 : pickup and delivery are consecutive stops in a block
        _case2(shift = shift, booking = booking)        
        # Case 3 : pickup in the last block, delivery becomes last stop in schedule
        _case3(shift = shift, booking = booking)        
        # Case 4 : pickup and delivery are separated by at least one stop
        _case4(shift = shift, booking = booking)


def _add_into_different_blocks(shift, booking):
    """
        Pick up is at the end of a work block while delivery is at the start of the next one
        D-1 possible insertions where D is the number of work blocks
    """
    pass

def _case0(shift, booking):
    """
        First insertion to the shift schedule
    """
    pass

def _case1(shift, booking):
    """
        Both the pickup and the delivery of booking are inserted at the end of the last work block, 
        so that the result would be those two stops would turn into the last two of the last work block
        Number of possible insertions = 1(at the end of the block only).
    """

    pass

def _case2(shift, booking):
    """
        Both the pick-up and the delivery of booking are inserted between two consecutive stops on the schedule-block
        Number of possible insertions = D*N(d) (D is the number of blocks and N(d) is the number of stops within the block d)
    """
    pass

def _case3(shift, booking):
    """
        The pick-up of booking takes place somewhere within the last work block, while its delivery is inserted at the end of the work-schedule
        Number of possible insertions = N
    """

    pass

def _case4(shift, booking):
    """
        The pick-up and delivery of booking are separated by at least one other stop and the delivery is not the last stop on the 
        expanded work schedule.
        Number of possible insertions = D*N(d)*(N(d)-1)/2 (D is the number of blocks and N(d) is the number of stops within the block d)
    """
    pass


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

def _find_best_shift_schedule(shift, booking) :
    pass

def _set_current_schedule():
    pass


############### INSERTION HEURISTICS ###############


def insertion_init(parameters = parameters, bookings = bookings, shifts = shifts):
            
    # Build an ordered priority queue of potential bookings to initialize a route
    # Bookings are sorted according to their earliest pick up time windows
    seed_bookings = bookings.sort(reverse = True)
    bookings_not_inserted = []

    # Process each booking 
    # While there are unprocessed bookings :
    while len(seed_bookings)>0 :

        booking_to_schedule = seed_bookings.pop()

        best_schedules = []

        # Generate the potential insertions of booking_to_schedule for each shift
        for shift in shifts :
            _new_potential_insertions(shift = shift, booking = booking_to_schedule)
            # Find the optimal schedule among each feasible schedule of the current shift
            best_schedule = _find_best_shift_schedule(shift = shift, booking = booking_to_schedule)

            if best_schedule != [inf]:
                best_schedule.append(shift)
                best_schedules.append(best_schedule)
            
        # Determine best overall schedule
        if best_schedules != []:
                best_schedules.sort()
                schedule = best_schedules[0]
                _set_current_schedule()
            else:
                bookings_not_inserted.append(booking_to_schedule)
        
        seed_bookings.remove(booking_to_schedule) 

            
# ---------------------------------------------------------------------
def get_si_algorithm():
    algo_name = "Insertion heuristic"
    algo_desc = "Mole & Jameson (1976) sequential cheapest insertion heuristic "+\
                "without local search (van Breedam 1994, 2002)"
    return (algo_name, algo_desc, insertion_init(parameters, bookings, shifts, node_to_station))
    
if __name__=="__main__":
    get_si_algorithm()
    pass


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