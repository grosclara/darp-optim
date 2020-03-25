#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from llist import dllist
from cli import *
from collections import namedtuple
from heapq import heappush, heappop
from logging import log, DEBUG
from util import objf, routes2sol

from data import sets, node_to_station, parameters, nb_bookings, bookings, shifts
from class_init import ShiftScheduleBlock


def _initialize_shift_schedules(shifts):
    schedules = {}
    for shift in shifts :
        schedules[shift] = new ShiftScheduleBlock(shift)
    return schedules


def _check_capacity_constraint(schedule, booking):
    #Return also the new capacity
    return True


def _check_ride_time_constraint(schedule, deviation):
    return True


def _check_turnover_constraint(schedule, booking):
    #Return also the new turnover
    return True

def _check_insertion_feasibility(schedule, booking):
    # Check time window capacity
    return True


def _compute_deviation(travel_time, node_before_pickup, node_before_drop_off, booking, schedule):
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


Insertion = namedtuple('Insertion', ['booking', 'node_before_pick_up', 'node_after_pickup',
                                    'node_before_drop_off', 'node_after_drop_off',
                                    'new_capacity', 'new_turnover'])

def _new_potential_insertions(schedule, booking, travel_time):

    # Initialisation of the pick up location
    node_before_pickup = schedule.route.first
    while node_before_pickup != schedule.route.last.prev:
        # Initialisation of the drop off location
        node_before_drop_off = node_before_pickup
        while node_before_drop_off != schedule.route.last:
            
            insertion_feasibility_checked = _check_insertion_feasibility(schedule, booking)
            
            if insertion_feasibility_checked :

                # Do not add infeasible insertions
                capacity_constraint_checked = _check_capacity_constraint(schedule, booking)
                turnover_constraint_checked = _check_turnover_constraint(schedule, booking)

                if capacity_constraint_checked & turnover_constraint_checked :
                    # Compute cost function
                    deviation = _compute_deviation(travel_time, node_before_pickup, node_before_drop_off, booking, schedule)
                    # Once the deviation time is computed, check the max ride time for each customer planned on this schedule
                    ride_time_constraint_checked = _check_ride_time_constraint(deviation, schedule)
                else :
                    continue

                if ride_time_constraint_checked:
                    # Add the potential insertions to the heap
                    # where to insert nodes, cost function value,
                    # Build the insertion for the heap

                    insertion = Insertion(customer, node_before_pick_up, node_before_pick_up.next, 
                                            node_before_drop_off, node_before_drop_off.next,
                                            new_capacity, new_turnover)
                    sorting_key = deviation
                    heappush( schedule.potential_insertion, (sorting_key, insertion) )
                
                else :
                    continue
            
            else : 
                continue

        # update potential drop off node insertion
        initial_drop_off_after = initial_drop_off_after.next
    # update potential pick up node insertion
    initial_pick_up_after = initial_pick_up_after.next
    

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


def parametrized_insertion_criteria(D, i, u, j, lm, mm):
    """ Mole and Jameson (1976) insertion criteria.
    
    i = insert after this customer / depot
    u = insert this customer 
    j = insert before this customer / depot
    
    * lm = lambda_multiplier (>=0) defines how strongly one prefers routes that
       visit just one customer.
    * mm = mu_multiplier (>=0)  is similar to the lambda of the savings algorithm. 
       It defines how much the edge that needs to be removed to make the  
       insertion weights when calculating the insertion cost.
    
    Note that we do this in one pass with min( -lambda*c_0_u + e(i,u,j) )
    instead of first calculating e(r,u,s) = min(e(i,u,j)) \forall i,j first and
    then computing  max( lambda*c_0_u - e(r,u,s) ) = max(sigma(i,u,s)).
    
    The reason is twofold. First, the best insertion position for u may be
    taken by other customer, which means that we should keep track on where
    to update it. Second the one pass scheme is equivalent, as the customer 
    with the best (maximal) criteria (l*) is always the best among different
    u as the c_0,u is the same \forall u therefore making the min(e(i,u,j)) 
    the decisive factor also in the one pass mode.
    """ 
    MST_c = D[i,u]+D[u,j]-mm*D[i,j]
    MSAV_c = lm*D[0,u]-MST_c
    return MSAV_c, MST_c


def insertion_init(bookings, shifts, initialize_routes_with, parameters):
    
    complete_routes = [] 
        
    # Build a ordered priority queue of potential route initialization bookings

    # Number of bookings not yet processed
    
    if initialize_routes_with=="earliest_pick_up_tw" :
        # Python3 doesn't support sort method on zip object
        seed_bookings = list(zip([booking.jobs[0].tw_start for booking in bookings], [booking.booking_id for booking in bookings]))
        seed_bookings.sort(reverse=True)
    elif initialize_routes_with=="latest_drop_off_tw" :
        seed_bookings = list(zip([booking.jobs[1].tw_end for booking in bookings], [booking.booking_id for booking in bookings]))
        seed_bookings.sort()
    else:
        raise ValueError("Unknown route initialization method '%s'"%initialize_routes_with)

    schedules = _initialize_shift_schedules(shifts)

        # while there are nodes to insert
        while len(seed_bookings)>0:
            booking_to_schedule = seed_bookings.pop()
            for shift in shifts :
                schedule = schedules[shift]     
                # Generate the list of insertion candidates
                if len(schedule.potential_insertions)==0:
                    """ # Initialisation of the pick up location
                    initial_pick_up_after = schedule.route.first
                    while initial_pick_up_after != schedule.route.last.prev:
                    # Initialisation of the drop off location
                        initial_drop_off_after = initial_pick_up_after
                        while initial_drop_off_after != route_datas.route.last:
                            _new_potential_insertions(booking_to_schedule , initial_pick_up_after , initial_drop_off_after)
                            initial_drop_off_after = initial_drop_off_after.next
                        initial_pick_up_after = initial_pick_up_after.next """

                    # Build a heap of all possible insertion of booking_to_schedule into the shift schedule
                    _new_potential_insertions(schedule.route, booking_to_schedule)
                    
                while len(route_datas.potential_insertions)>0:
                    insertion_succesfull = False
                    # unpack a best candidate from the insertion queue
                    _, insertion = heappop(route_datas.potential_insertions)
                
                    # Check if it *seems* OK to insert
                    # - The node has been already inserted somewhere
                    # - Something else has already been inserted here, ignore
                    # - And check if inserting would break the C constraint
                    is_ok =  _seems_valid_insertion(insertion, route_datas.used_capacity,
                                                unrouted, D, d, C)
                    if not is_ok:
                        continue
                
                    if __debug__:
                        log(DEBUG-2,"Try insertion %d-%d-%d with l_delta %.2f"% (
                             insertion.after_node.value, insertion.customer,
                            insertion.before_node.value, insertion.cost_delta))
                   
                    # It is all OK to insert the customer (check L constraint)?
                    insertion_succesfull, new_edges = insert_callback(insertion,
                                                                  rd,D,L,
                                                                  minimize_K)
                    
                    if insertion_succesfull:
                        unrouted.remove(insertion.customer)
                        for from_node, to_node in new_edges:
                            # insertion changes the route -> new insertions possible
                            # update the route_datas
                            _new_potential_insertions(unrouted, D, d, C, L, rd,
                                                  from_node, to_node,
                                                  insertion_strain_callback)
                
                        if __debug__:
                            log(DEBUG,"Chose to insert n%d resulting in route %s (%.2f)"%
                                       (insertion.customer, str(list(rd.route)), rd.cost))
                        break
                    else:
                        if __debug__:
                            log(DEBUG-3,"Insertion of n%d would break L constraint."%
                                insertion.customer)
                        continue
                        
            # if are not able to add any more customers to the route,
            #  so start a new route
            insertions_exhausted = len(rd.potential_insertions)==0
            if insertions_exhausted and len(unrouted)>0:
                if __debug__:
                    log(DEBUG,"Route #%d finished as %s (%.2f)"%
                        (k, str(list(rd.route)), rd.cost))
                complete_routes.append(rd)

                # Some seed initializations rely on the state of the completed
                #  routes. Then, we can use initialize_routes_with callback 
                #  to generate more seed(s).
                if not seed_customers:
                    if callable(initialize_routes_with):
                        seed_customers = initialize_routes_with(D, unrouted,
                                                                complete_routes)
                    else:
                        raise StopIteration("Ran out of seed nodes before all"+
                                            "customers were routed")
                
                rd = _initialize_new_route(seed_customers, unrouted, D, d)
                if __debug__:
                    log(DEBUG, "Initialized a new route #%d %s"%
                               (route_index, str(list(rd.route))))
    
                route_datas[route_index] = rd    
                              
    return [0]+_EmergingRouteData.export_solution(route_datas)\
              +_EmergingRouteData.export_solution(complete_routes)


# ---------------------------------------------------------------------
# Wrapper for the command line user interface (CLI)
def get_si_algorithm():
    algo_name = "Insertion heuristic"
    algo_desc = "Mole & Jameson (1976) sequential cheapest insertion heuristic "+\
                "without local search (van Breedam 1994, 2002)"
    def call_init(parameters, bookings, shifts, initialize_routes_with):
        return insertion_init(parameters, bookings, shifts, initialize_routes_with)
    
    return (algo_name, algo_desc, call_init)

if __name__=="__main__":
    get_si_algorithm()
