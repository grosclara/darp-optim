import json
from math import inf

from data.format_data import sets, parameters, nb_bookings, node_to_station, shifts, bookings, jobs_dict
from data.models import *


################### OPTIMIZATION COST ###################

def cost_shedule(schedule, travel_time) :
    s = 0
    for k in range(len(schedule.route) - 1):
        s += travel_time[node_to_station[schedule.route[k]["Job"].job_id],
                         node_to_station[schedule.route[k+1]["Job"].job_id]]
    return s


def global_cost(schedules, travel_time) :
    s = 0
    for shift in schedules :
        s += cost_shedule(schedules[shift], travel_time)
    return s


################### CONSTRAINT CHECKS ###################

def _check_capacity_constraint(schedule, booking, index_before_pick_up, index_before_drop_off):
    
    index = index_before_pick_up + 1

    # If pick up and drop off are consecutive nodes
    if index_before_pick_up == index_before_drop_off:
        used_capacity = schedule.route[index]["Used capacity"] + booking.passengers
        return used_capacity <= schedule.shift.capacity

    else:
        stop_to_drop_off = False
        while index != index_before_drop_off + 1:
            used_capacity = schedule.route[index]["Used capacity"] + booking.passengers
            if not used_capacity <= schedule.shift.capacity:
                return False
            index += 1

    return True


def _check_time_slot_constraint_same_node(travel_time, index_before_pick_up, schedule, booking):

    jobs_before = []
    jobs_after = []
    AT_before_pickup = schedule.route[index_before_pick_up]['Arrival time']
    AT_results = {}

    for node in schedule.route:
        AT_node = node['Arrival time']

        if AT_node <= AT_before_pickup:
            jobs_before.append(node['Job'])
            AT_results[node['Job'].job_id] = node["Arrival time"]

        else:
            jobs_after.append(node["Job"])

    time_route = AT_before_pickup + schedule.route[index_before_pick_up]["Job"].duration

    time_route += travel_time[node_to_station[schedule.route[index_before_pick_up]["Job"].job_id],
                              node_to_station[booking.jobs[0].job_id]]

    if time_route < booking.jobs[0].tw_start:
        time_route = booking.jobs[0].tw_start

    elif time_route > booking.jobs[0].tw_end :
        # Invalid time windows contraint
        return False, None

    AT_results[booking.jobs[0].job_id] = time_route
    time_route += booking.jobs[0].duration

    time_route += travel_time[node_to_station[booking.jobs[0].job_id],
                              node_to_station[booking.jobs[1].job_id]]
    AT_results[booking.jobs[1].job_id] = time_route
    time_route += booking.jobs[1].duration

    for k in range(len(jobs_after)):

        if k == 0:
            job_before = booking.jobs[1]

        else:
            job_before = jobs_after[k - 1]

        job = jobs_after[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        
        if time_route < job.tw_start :
            time_route = job.tw_start

        elif time_route > job.tw_end :
            return False, None

        AT_results[job.job_id] = time_route
        time_route += job.duration

    return True, AT_results


def _check_time_slot_constraint(travel_time, index_before_pick_up, index_before_drop_off, schedule, booking):
    """
        This function will return the AT (arrival time) of the client to insert
        The impacted customers are all customers exepct those whose drop off is before the pick up to insert
        We look at the events independently of whether they are drop-offs or pick-ups.
        They are 3 cases :
            event <= node_before_pickup : no change bookings_before
            node_before_pickup < event <= node_before_drop_off : pick-up bookings_between deviation offset
            node_before_drop_off < event : pick-up offset + drop_off bookings_after
        We must not forget the hypothesis that the car had stopped at a station to wait for a customer -> we must calculate the time of the new
        itinerary without starting from the AT
    """

    if index_before_pick_up == index_before_drop_off :
        return _check_time_slot_constraint_same_node(travel_time, index_before_pick_up, schedule, booking)

    jobs_before = []
    jobs_between = []
    jobs_after = []
    AT_before_pick_up = schedule.route[index_before_pick_up]['Arrival time']
    AT_before_drop_off = schedule.route[index_before_drop_off]['Arrival time']
    AT_results = {}

    for node in schedule.route:
        AT_node = node['Arrival time']
        if AT_node <= AT_before_pick_up:
            jobs_before.append(node["Job"])
            AT_results[node['Job'].job_id] = node["Arrival time"]
        elif AT_node <= AT_before_drop_off:
            jobs_between.append(node["Job"])
        else:
            jobs_after.append(node["Job"])

    # We add the time taken to go to the pick up node
    time_route = AT_before_pick_up + schedule.route[index_before_pick_up]["Job"].duration
    
    time_route += travel_time[node_to_station[schedule.route[index_before_pick_up]["Job"].job_id],
                              node_to_station[booking.jobs[0].job_id]]
    if time_route < booking.jobs[0].tw_start:
        time_route = booking.jobs[0].tw_start
    elif time_route > booking.jobs[0].tw_end:
        # Situation not feasible
        return False, None

    AT_results[booking.jobs[0].job_id] = time_route
    time_route += booking.jobs[0].duration

    for k in range(len(jobs_between)):
        if k == 0:
            job_before = booking.jobs[0]
        else:
            job_before = jobs_between[k - 1]
        job = jobs_between[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]
        if time_route < job.tw_start:
            time_route = job.tw_start + job.duration
        elif time_route > job.tw_end:
            return False, None
        AT_results[job.job_id] = time_route
        time_route += job.duration

    # Ensure the insertion is feasbile for jobs after the pick up
    time_route += travel_time[
        node_to_station[schedule.route[index_before_drop_off]["Job"].job_id],
        node_to_station[booking.jobs[1].job_id]]

    if time_route < booking.jobs[1].tw_start:
        time_route = booking.jobs[1].tw_start

    elif time_route > booking.jobs[1].tw_end:
        # Infeasible
        return False, None

    AT_results[booking.jobs[1].job_id] = time_route
    time_route += booking.jobs[1].duration

    for k in range(len(jobs_after)):
        if k == 0:
            job_before = booking.jobs[1]
        else:
            job_before = jobs_after[k - 1]
        job = jobs_after[k]
        time_route += travel_time[node_to_station[job_before.job_id], node_to_station[job.job_id]]

        if time_route < job.tw_start:
            time_route = job.tw_start

        elif time_route > job.tw_end:
            # Infeasible
            return False, None

        AT_results[job.job_id] = time_route
        time_route += job.duration

    return True, AT_results


def _check_ride_time_constraint(travel_time, index_before_pick_up, index_before_drop_off, schedule, booking):
    """
    :param travel_time: Table indexed on stations
    :param index_before_pickup
    :param index_before_drop_off
    :param schedule: Actual shift schedule
    :param booking: Booking object we want to insert
    :return: (Boolean, int, AT_results) True if the insertion is feasible regarding the ride time and time windows constraints : the corresponding int is the insertion cost and the AT_results is the arrival time at each stop list
    """

    cost = 0

    insertion_feasibility, AT_results = _check_time_slot_constraint(travel_time, index_before_pick_up,
                                                                    index_before_drop_off, schedule, booking)
    
    if not insertion_feasibility:
        return False, None, None

    for job_id in AT_results:
        if job_id != 0 and job_id != 2*nb_bookings+1:
            job = jobs_dict[job_id]
            if job.specie == "PickUpJob":
                ride_time = AT_results[nb_bookings + job_id] - AT_results[job_id]
                cost += ride_time * job.passengers
                if ride_time > job.max_duration:
                    return False, None, None

    return True, cost, AT_results


def _check_turnover_constraint(schedule, booking):

    # If feasible, return also the new turnover
    if schedule.turnover + booking.price > schedule.shift.max_turnover :
        return False, None

    new_turnover = schedule.turnover + booking.price

    return True, new_turnover


def _check_insertion_feasibility(travel_time, indice_before_pickup, indice_before_drop_off, schedule, booking):
    """
    :param travel_time: tableau indexé sur les numéros des stations
    :param node_before_pickup: de type node avec node.value de type {"Job":BookingJob,"Used capacity": int , "Arrival time": int, "Departure time": int}
    :param node_before_drop_off : de type node avec node.value de type {"Job":BookingJob,"Used capacity": int , "Arrival time": int, "Departure time": int}
    :param schedule: objet de type avec schedule.route liste de dictionnaire
                    [ ... {"Job":BookingJob,"Used capacity": int , "Arrival time": int, "Departure time": int} ...]
    :param booking: de type Booking, (c'est le booking qu'on veut insérer

    :return: True, cost  si on peur insérer booking à cet endroit
    """

    # on vérifier des contraintes les moins couteuses en calcules aux plus couteuses :
    turnover_checked, new_turnover = _check_turnover_constraint(schedule, booking)
    if not turnover_checked:
        return False, None, None, None
    if not _check_capacity_constraint(schedule, booking, indice_before_pickup, indice_before_drop_off):
        return False, None, None, None
    ride_time_and_time_slot, cost, AT_results = _check_ride_time_constraint(travel_time, indice_before_pickup,
                                                                            indice_before_drop_off, schedule, booking)
    return ride_time_and_time_slot, cost, AT_results, new_turnover


################### INSERTION AND UPDATE ###################


def _insertion_same_node(index_before_pick_up, schedule, booking, new_turnover, AT_results, new_cost):
    new_route = []

    # Copy the first schedule before the insertion of the pickup node
    for k in range(index_before_pick_up + 1):
        new_route.append(schedule.route[k].copy())

    used_capacity = schedule.route[index_before_pick_up]["Used capacity"] + booking.passengers

    # Build and add the pick up to the new route
    node_pickup = {"Job": booking.jobs[0], "Used capacity": used_capacity,
                   "Arrival time": AT_results[booking.jobs[0].job_id],
                   "Departure time": AT_results[booking.jobs[0].job_id] + booking.jobs[0].duration}
    new_route.append(node_pickup)

    used_capacity = schedule.route[index_before_pick_up]["Used capacity"]

    # Build and add the drop off node to the new route
    node_drop_off = {"Job": booking.jobs[1], "Used capacity": used_capacity,
                     "Arrival time": AT_results[booking.jobs[1].job_id],
                     "Departure time": AT_results[booking.jobs[1].job_id] + booking.jobs[1].duration}
    new_route.append(node_drop_off)

    # Copy the end of the route after drop off
    for k in range(index_before_pick_up + 1, len(schedule.route)):
        new_node = schedule.route[k].copy()
        new_node["Arrival time"] = AT_results[schedule.route[k]["Job"].job_id]
        new_node["Departure time"] = new_node["Arrival time"] + schedule.route[k]["Job"].duration
        new_route.append(new_node)

    results = {"route": new_route, "turnover": new_turnover, "cost": new_cost}
    new_schedule = ShiftScheduleBlock(schedule.shift, results)

    return new_schedule


def _insertion(index_before_pick_up, index_before_drop_off, schedule, booking, new_turnover, AT_results, new_cost):
    """
        Insert and update booking into schedule
    """
    # If the nodes are inserted consecutively
    if index_before_pick_up == index_before_drop_off:
        new_schedule =  _insertion_same_node(index_before_pick_up, schedule, booking, new_turnover, AT_results, new_cost)

    else : 

        new_route = []

        # Copy the route before the insertion of the pick up node
        for k in range(index_before_pick_up + 1):
            new_route.append(schedule.route[k].copy())

        # Add the pick up node and compute its "Used capacity"
        used_capacity = schedule.route[index_before_pick_up]["Used capacity"] + booking.passengers
        node_pickup = {"Job": booking.jobs[0], "Used capacity": used_capacity,
                    "Arrival time": AT_results[booking.jobs[0].job_id],
                    "Departure time": AT_results[booking.jobs[0].job_id] + booking.jobs[0].duration}
        new_route.append(node_pickup)

        # Update the arrival, departure and used capacity of each node between pick up and drop off
        for k in range(index_before_pick_up + 1, index_before_drop_off + 1):
            new_node = schedule.route[k].copy()
            new_node["Used capacity"] += booking.passengers
            new_node["Arrival time"] = AT_results[schedule.route[k]["Job"].job_id]
            new_node["Departure time"] = new_node["Arrival time"] + schedule.route[k]["Job"].duration
            new_route.append(new_node)

        # Add the drop off node and compute its "Used capacity"
        used_capacity = schedule.route[index_before_drop_off]["Used capacity"] - booking.passengers
        node_drop_off = {"Job": booking.jobs[1], "Used capacity": used_capacity,
                        "Arrival time": AT_results[booking.jobs[1].job_id],
                        "Departure time": AT_results[booking.jobs[1].job_id] + booking.jobs[1].duration}
        new_route.append(node_drop_off)

        # UPdate the route (arrival and departure time) after the insertion of the drop off node
        for k in range(index_before_drop_off + 1, len(schedule.route)):
            new_node = schedule.route[k].copy()
            new_node["Arrival time"] = AT_results[schedule.route[k]["Job"].job_id]
            new_node["Departure time"] = new_node["Arrival time"] + schedule.route[k]["Job"].duration
            new_route.append(new_node)

        results = {"route": new_route, "turnover": new_turnover, "cost": new_cost}
        new_schedule = ShiftScheduleBlock(schedule.shift, results)

    return new_schedule


def _new_potential_insertions(schedule, booking, travel_time):
    opt_cost = inf
    opt_schedule = None
    feasibility = False

    # Initialisation of the pick up location
    for index_before_pick_up in range(len(schedule.route) - 1):
        # Initialisation of the drop off location
        for index_before_drop_off in range(index_before_pick_up, len(schedule.route) - 1) :
            insertion_feasibility, cost, AT_results, new_turnover = \
                _check_insertion_feasibility(travel_time, index_before_pick_up, index_before_drop_off, schedule,
                                             booking)

            if insertion_feasibility :
                # add_cost represents only the cost of the insertion
                # cost is the whole route cost
                add_cost = cost

            if insertion_feasibility and add_cost < opt_cost :
                feasibility = True
                opt_schedule = _insertion(index_before_pick_up, index_before_drop_off, schedule, booking,
                                            new_turnover, AT_results, cost)
                opt_cost = add_cost

    return feasibility, opt_schedule, opt_cost


################### INITIALIZATION ###################


def _initialize_shift_schedules(shifts):
    schedules = {}
    for shift in shifts:
        schedules[shift] = ShiftScheduleBlock(shift, {})
    return schedules


def insertion_init(bookings, shifts, travel_time = parameters["time_table_dict"], sort = True):

    # Build a ordered priority queue of potential route initialization bookings
    if sort :
        bookings.sort()
        shifts.sort()

    # Number of bookings not yet processed
    nb_assigned_bookings = 0
    
    schedules = _initialize_shift_schedules(shifts)

    turnover = {}
    for shift in shifts :
        turnover[shift] =  0

    # While there are nodes to insert
    while len(bookings) > 0:
        booking_to_schedule = bookings.pop()
        
        opt_cost = inf
        opt_schedule = None
        feasibility = False

        for shift in shifts :
            schedule = schedules[shift]
            feasibility_shift, schedule_shift, cost_shift = _new_potential_insertions(schedule, booking_to_schedule, travel_time)
            if feasibility_shift:
                feasibility = True
                if cost_shift < opt_cost :
                    opt_cost = cost_shift
                    opt_schedule = schedule_shift

        if feasibility:
            turnover[opt_schedule.shift] += booking_to_schedule.price
            schedules[opt_schedule.shift] = opt_schedule
            nb_assigned_bookings += 1

    return schedules


############ JSON FORMATTING ############

def json_formatting(schedules, file_name):
    
    res_shifts = []
    nb_assigned = 0
    travel_time = parameters["time_table_dict"]

    for shift_indice in schedules :
        res_shift = []
        schedule = schedules[shift_indice]

        for job_indice in range(len(schedule.route)) :
            id = schedule.route[job_indice]["Job"].long_id
            AT = schedule.route[job_indice]["Arrival time"]
            res_shift.append({"id" : id, "time": AT})
            nb_assigned += 0.5
        nb_assigned = (nb_assigned-1)
        res_shifts.append({"id" :  int(schedule.shift.long_id), "jobs" : res_shift})

    route_cost = global_cost(schedules, travel_time)
    res3 = {"nb_assigned_bookings": int(nb_assigned), "route_cost": route_cost, "shifts": res_shifts}

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(res3, f, indent=4)

if __name__ == '__main__' : 
    
    schedules = insertion_init(bookings, shifts, parameters["time_table_dict"], True)
    json_formatting(schedules, "results/insertion_v2_week_v2.json")


