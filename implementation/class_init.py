class Booking:
    def __init__(self, long_id, booking_id, price, max_duration, passengers, jobs):
        self.long_id = long_id
        self.booking_id = booking_id
        self.price = price
        self.max_duration = max_duration
        self.passengers = passengers
        self.jobs = jobs

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

class ShiftScheduleBlock:
    """ A data structure to keep all of the data of the route that is being
    constructed in the same place. """

    def __init__(self, shift):
        
        self.shift = shift # Shift object (capacity, max_turnover)

        self.potential_insertions = []

        self.bookings_processed = []

        # Route objet : job dans un job : time window capacity
        self.route = dllist([{"Job":shift.jobs[0],"Used capacity":0},{"Job":shift.jobs[1],"Used capacity":0}]) #Dépot
        self.turnover = 0
        self.cost = 0

"""
        if seed_customer:
            lroute = [0]+seed_customers+[0]
            self.route = dllist(lroute)
            self.cost = objf(lroute, D)
            self.used_capacity = sum(d[n] for n in lroute) if d else 0
        else:
            self.route = dllist([0,0])
            self.used_capacity = 0
            self.cost = 0
            
    @staticmethod
    def export_solution(route_datas):
        sol = []
        for rd in route_datas:
            if rd and len(rd.route)>2:
                sol += list(rd.route)[1:]
        return sol
 """