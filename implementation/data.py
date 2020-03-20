import json

import pandas
import numpy
import json
from implementation.class_init import Booking, BookingJob, Shift, ShiftJob

with open("data/toy_dataset.json") as json_data:
# with open("data/day_data.json") as json_data:
    data_dict = json.load(json_data)

# BOOKING LIST
nb_bookings = len(data_dict['bookings'])

bookings = []
count = 1  # Give a proper job id
for booking in data_dict['bookings']:
    jobs = []
    for job in booking['jobs']:

        # Create the job_id attribute
        if job['type'] == "PickUpJob":
            job_id = count
        else:
            job_id = count + nb_bookings

        # Retrieve the station
        station = int(job['station'][1:])

        # Create the BookingJob object
        j = BookingJob(job['id'], job_id, job['type'],
                       job['timeWindowBeginDate'], job['timeWindowEndDate'],
                       job['duration'], job['latitude'], job['longitude'],
                       station)

        # Add the job to the job list
        jobs.append(j)

    # Create the Booking object
    b = Booking(booking['id'], count, booking['price'],
                booking['maximumDuration'], booking['passengers'], jobs)

    count += 1
    # Add the Booking b to the booking list
    bookings.append(b)

# print(bookings,nb_bookings)

# SHIFT LIST
shifts = []
nb_shifts = len(data_dict['shifts'])

for shift in data_dict['shifts']:
    jobs = []
    for job in shift['jobs']:
        # Create the ShiftJob object
        j = ShiftJob(job['id'], job['type'], job['timeDate'],
                     job['latitude'], job['longitude'], job['station'])

        # Add the job to the jobs list
        jobs.append(j)

    # Create the Shift object
    s = Shift(shift['id'], shift['capacity'],
              shift['maximumTurnover'], jobs)
    # Add the Shift s to the shift list
    shifts.append(s)

# print(shifts,nb_shifts)

# TRAVEL TIMES
time_data = pandas.read_csv("data/toy_travel_times.csv", sep=';')
# time_data = pandas.read_csv("data/travel_times.csv", sep=';')
nb_stations = len(time_data)

# Matrix where time_table[i,j] is the travel time from station i to j
time_table_dict = {}

for i in range(nb_stations):
    for j in range(nb_stations):
        time_table_dict[i, j] = int(time_data["s{}".format(i)][j])

# print(time_table_dict)

# SETS

# List of drivers'id
shift_set = [shifts[k].long_id for k in range(nb_shifts)]
# print(driver_set)

# [1, ..., 25]
pick_up_set = [k for k in range(1, nb_bookings + 1)]
# print(pick_up_set)

# [26, ..., 50]
drop_off_set = [k for k in range(nb_bookings + 1, 2 * nb_bookings + 1)]
# print(drop_off_set)

# [1, ..., 50]
pud_set = pick_up_set + drop_off_set
# print(pud_set)

# List of pick_up, drop_off and warehouse (station 0 and 2n+1)
# [0, ..., 51]
node_set = [0] + pick_up_set + drop_off_set + [2 * nb_bookings + 1]
# print(node_set)

# List of stations to compute travel times
# [0, ..., 52]
station_set = [k for k in range(nb_stations)]
# print(station_set)

# To retrieve the time travel given elements in node_set, there's a need to 
# retrieve the corresponding station
# A key correspond to a node and the value is the corresponding station
# {1: 16, 26: 1, 2: 18, 27: 19, ..., 25: 16, 50: 10, 0: 0, 51: 0}
node_to_station = {}
for k in range(nb_bookings):
    # Retrieve the station attribute from the k-th request
    node_to_station[k + 1] = bookings[k].jobs[0].station
    node_to_station[nb_bookings + k + 1] = bookings[k].jobs[1].station
# Associate the warehouse (keys 0 and 2n+1) to station 0
node_to_station[0] = 0
node_to_station[2 * nb_bookings + 1] = 0

# print(node_to_station)

sets = {'shift': shift_set, "pick_up": pick_up_set, "drop_off": drop_off_set, "pud": pud_set, "node": node_set,
        "station": station_set}

# PARAMETERS

# Correspond to the var e : the execution duration is defined at each station 
# (node_set)
duration_dict = {}
for booking in bookings:
    for job in booking.jobs:
        duration_dict[job.job_id] = job.duration
duration_dict[0] = duration_dict[2 * nb_bookings + 1] = 0
# print(duration_dict)

# Correspond to the var r : the booking cost is defined at each pick
# up and drop off station (pud_set)
price_dict = {}
for booking in bookings:
    for job in booking.jobs:
        if job.job_id <= nb_bookings:
            price_dict[job.job_id] = booking.price
# print(price_dict)

# Correspond to the var m_max : the maximum duration of a booking is defined at 
# each pick up station (pick_up_set)
max_duration_dict = {}
for booking in bookings:
    max_duration_dict[booking.booking_id] = booking.max_duration
# print(max_duration_dict)

# Correspond to the var q_req : the passengers entering or leaving the vehicule
# is defined at each node (node_set)
passengers_dict = {}
for booking in bookings:
    passengers_dict[booking.booking_id] = booking.passengers
    passengers_dict[booking.booking_id + nb_bookings] = -booking.passengers
# At the warehouses, no passenger enter nor leave the vehicule
passengers_dict[0] = 0
passengers_dict[2 * nb_bookings + 1] = 0
# print(passengers_dict)

# Correspond to the var C : the maximum capacity of each vehicule is defined on
# the driver_set
capacity_dict = {}
for shift in shifts:
    capacity_dict[shift.long_id] = shift.capacity
# print(capacity_dict)  

# Correspond to the var R : the maximum turnover of each driver is defined on
# the driver_set
max_turnover_dict = {}
for driver in shifts:
    max_turnover_dict[driver.long_id] = driver.max_turnover
# print(max_turnover_dict)

# Correspond to the var tw_driver (L,U) : the time window of each vehicule
# is defined on the driver_set
# {3238042: (45000, 58800), ..., 3237783: (31200, 41400)}
tw_driver_dict = {}
for driver in shifts:
    tw_driver_dict[driver.long_id] = (driver.jobs[0].time_date, driver.jobs[1].time_date)
# print(tw_driver_dict)

# Correspond to the var tw (l,u) : (BEWARE!) the time window of each booking is 
# defined on the node_set
# {1: (42600, 43500), 26: (42600, 45143), ... , 25: (42300, 43200), 50: 
# (42300, 44707), 0: (31200, 65467), 51: (31200, 65467)}
tw_dict = {}
# Compute each tw for pick up and drop off nodes
for booking in bookings:
    for job in booking.jobs:
        tw_dict[job.job_id] = (job.tw_start, job.tw_end)

# Compute tw at warehouses stations
# Compute l_0,u_0
l_i0 = min(tw_dict[i][0] for i in range(1, 2 * nb_bookings + 1))
t_start = min(time_table_dict[0, i] for i in range(1, nb_stations))
L_k0 = min(tw_driver_dict[shifts[k].long_id][0] for k in range(nb_shifts))

u_i0 = max(tw_dict[i][1] for i in range(1, 2 * nb_bookings + 1))
t_end = max(time_table_dict[i, nb_stations-1] for i in range(1, nb_stations))
U_k0 = max(tw_driver_dict[shifts[k].long_id][1] for k in range(nb_shifts))

l_0 = max(0, min(l_i0 - t_start, L_k0))
u_0 = max(u_i0 + t_end, U_k0)

tw_dict[0] = (l_0, u_0)
tw_dict[2 * nb_bookings + 1] = (l_0, u_0)

# print(tw_dict[1][0])

parameters = {"time_table_dict": time_table_dict, "duration_dict": duration_dict, "price_dict": price_dict,
              "max_duration_dict": max_duration_dict, "passengers_dict": passengers_dict,
              "capacity_dict": capacity_dict, "max_turnover_dict": max_turnover_dict, "tw_driver_dict": tw_driver_dict,
              "tw_dict": tw_dict}
# print(parameters)
