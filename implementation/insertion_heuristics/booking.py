class Booking:

    def __init__(self, long_id, booking_id, price, max_duration, passengers, jobs, drt):
        
        self.long_id = long_id
        self.booking_id = booking_id
        self.price = price
        self.max_duration = max_duration # Maximal ride time
        self.passengers = passengers
        self.jobs = jobs

        self.drt = drt

        self.disutility = 0
        self.newDisutility = 0

    
    def getEPT(self): # Earliest pick up time
        return self.jobs[0].tw_start
    
    def getLPT(self): # Latest pick up time
        return self.jobs[0].tw_end

    def getEDT(self): # Earliest delivery time
        return self.jobs[1].tw_start

    def getLDT(self) # Latest delivery time
        return self.jobs[1].tw_end
    
    def getDPT(self) # Desired pick up time
        return self.getEPT()
    
    def getDirectRideTime(self) :
        return self.drt

    def getDisutility(self) :
        retun self.disutility

    def getPickUp(self):
        return self.jobs[0]

    def getDropOff(self):
        return self.jobs[1]

    def __lt__(self, other):
        return self.getEPT() < other.getEPT()

    def __repr__(self):
        return str(self.long_id)