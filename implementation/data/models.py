from math import inf

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
        return str(self.jobs)


class BookingJob:
    def __init__(self, long_id, booking_id, job_id, specie, tw_start, tw_end, duration, latitude, longitude, station, max_duration, passengers):
        self.long_id = long_id
        self.booking_id = booking_id
        self.job_id = job_id
        self.specie = specie
        self.tw_start = tw_start
        self.tw_end = tw_end
        self.duration = duration
        self.GPS = (latitude, longitude)
        self.station = station
        self.max_duration = max_duration
        if specie == "DropOffJob" :
            self.passengers = -passengers
        else :
            self.passengers = passengers

    def __repr__(self):
        return str(self.job_id)


class Shift:
    def __init__(self, long_id, capacity, max_turnover, jobs, nb_bookings):
        self.long_id = long_id
        self.capacity = capacity
        self.max_turnover = max_turnover
        self.jobs = jobs
        self.nb_bookings = nb_bookings

        self.reformat_shift_jobs()

    def reformat_shift_jobs(self) :
        """
            Transform shift jobs into BookingJob object
        """
        self.formatted_jobs = []
        for job in self.jobs :
            if job.specie == "ShiftBegin" :
                job_id = 0
                specie = "PickUpJob"
                tw_start = job.time_date
                tw_end = inf
            else :
                job_id = 2*self.nb_bookings+1
                specie = "DropOffJob"
                tw_start = 0
                tw_end = job.time_date

            booking_job = BookingJob(job.long_id, -1, job_id, specie, tw_start, tw_end, 0, \
                job.GPS[0], job.GPS[1], job.station, inf, 0)
            
            self.formatted_jobs.append(booking_job)
    
    def __lt__(self, other):
        return self.jobs[0].time_date < other.jobs[0].time_date

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

    def __init__(self, shift, results):
        
        self.shift = shift # Shift object

        if results == {}:
            self.route = [{"Job": shift.formatted_jobs[0], "Used capacity" : 0, "Arrival time" : shift.formatted_jobs[0].tw_start, "Departure time" : shift.formatted_jobs[0].tw_start},
                             {"Job": shift.formatted_jobs[1], "Used capacity" : 0, "Arrival time" : shift.formatted_jobs[1].tw_end, "Departure time" : shift.formatted_jobs[1].tw_end}]
            self.turnover = 0
            self.cost = 0
        else :
            self.route = results["route"]
            self.turnover = results["turnover"]
            self.cost = results["cost"]


    def update(self, route, turnover, cost):
        self.route = route
        self.turnover = turnover
        self.cost = cost

    def __repr__(self):
        return str(self.route)



class Individual :
    
    def __init__(self, indice, M, schedules, fitness) :
        self.M = M
        self.schedules = schedules
        self.fitness = fitness
        self.indice = indice

    def update(self, schedules, fitness):
        self.schedules =  schedules
        self.fitness = fitness

    def __repr__(self):
        s = "Indice " + str(self.indice) + " cost " + str(self.fitness)
        return s

    def copie(self):
        ind = Individu(self.indice, copy(self.M), self.schedules, self.fitness)
        return ind


