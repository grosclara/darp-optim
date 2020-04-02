class Booking:
    def __init__(self, long_id, booking_id, price, max_duration, passengers, jobs):
        self.long_id = long_id
        self.booking_id = booking_id
        self.price = price
        self.max_duration = max_duration
        self.passengers = passengers
        self.jobs = jobs

    def __lt__(self, other):
        return self.jobs[1].tw_start < other.jobs[1].tw_start

    def __repr__(self):
        return str(self.long_id)


class BookingJob:
    def __init__(self, long_id, booking_id, job_id, specie, tw_start, tw_end, duration, latitude, longitude, station):
        self.long_id = long_id
        self.booking_id = booking_id
        self.job_id = job_id
        self.specie = specie
        self.tw_start = tw_start
        self.tw_end = tw_end
        self.duration = duration
        self.GPS = (latitude, longitude)
        self.station = station

    def __repr__(self):
        return str(self.long_id)


class Shift:
    def __init__(self, long_id, capacity, max_turnover, jobs):
        self.long_id = long_id
        self.capacity = capacity
        self.max_turnover = max_turnover
        self.jobs = jobs

    def __repr__(self):
        return str(self.long_id)


class ShiftJob:
    def __init__(self, long_id, specie, time_date, latitude, longitude, station):
        self.long_id = long_id
        self.specie = specie
        self.time_date = time_date
        self.GPS = (latitude, longitude)
        self.station = station

    def __repr__(self):
        return str(self.long_id)

from llist import dllist

class ShiftScheduleBlock:
    """ A data structure to keep all of the data of the route that is being
    constructed in the same place. """

    def __init__(self, shift):
        
        self.shift = shift # Shift object (capacity, max_turnover)

        self.potential_insertions = []

        self.bookings_processed = []

        # Route objet : job dans un job : time window capacity
        self.warehouse = 0
        self.route = dllist([{"Job":shift.jobs[0],"Used capacity":0, "Scheduled time":0},{"Job":shift.jobs[1],"Used capacity":0, "Scheduled time":0}]) #Dépot
        self.turnover = 0
        self.cost = 0

# class ShiftStop:
#     def __init__(self, job, capacity, arrival_time, departure_time):
#         self.job = job
#         self.capacity = capacity
#         self.arrival_time = arrival_time
#         self.departure_time = departure_time

from collections import namedtuple

Insertion = namedtuple('Insertion', ['booking', 'node_before_pick_up', 'node_before_drop_off','deviation'])