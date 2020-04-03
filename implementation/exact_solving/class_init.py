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