class Darp:

    def __init__(self, bookings, shifts):
        bookings.sort()
        self.bookings = bookings
        self.shifts = shifts
        self.bookingsNotInserted = []

    #utilitiy constants :
        self.constants=dict()
        self.constants["c1"]=1
        self.constants["c2"]=1
        self.constants["c3"]=1
        self.constants["c4"]=1
        self.constants["c5"]=1
        self.constants["c6"]=1
        self.constants["c7"]=1
        self.constants["c8"]=1
        self.constants["W1"]=60
        self.constants["W2"]=60
    
    def createSchedules(self):
        self.bookingsNotInserted = []
        for i in range(len(self.bookings)):
            bestSchedules=[]
            for j in range(len(self.shifts)):
                self.addToShift(self.bookings[i],self.shifts[j])
                bestSchedule = self.findBestShiftSchedule(self.shifts[j],self.bookings[i])
                if bestSchedule != [float("inf")]: # Determine best overall schedule
                    bestSchedule.append(j)
                    bestSchedules.append(bestSchedule)
            if bestSchedules != []:
                bestSchedules.sort()
                schedule = bestSchedules[0]
                self.shifts[schedule[2]].setCurrentSchedule(schedule[1])
            else:
                self.bookingsNotInserted.append(self.bookings[i])

    def addToShift(self,booking,shift):
        shift.addIntoSameBlock(booking,self)
        shift.addIntoDifferentBlocks(booking)
    
    def findBestShiftSchedule(self,shift,booking):

        bestInsertion = [float("inf")]
        feasInserts = shift.getFeasibleSchedules()
        for schedule in feasInserts:
            self.scheduleOptimisation(schedule,booking)
            incDisutility = self.calcIncrementalCost(schedule,booking,shift)
            bestInsertion = min(bestInsertion,[incDisutility,schedule])
        return bestInsertion
    
    def scheduleOptimisation(self, schedule, booking):
        I=0
        if len(schedule)==1:
            I=0
        elif booking in schedule[0]:
            I=-1
        elif booking in schedule[-1]:
            I=1

        Rmin=0
        Amax=float("inf")
        deviation=0
        nbrOfCustomers=0
        for block in schedule:
            block.calcAandR()
            Rmin=max(block.getR(),Rmin)
            Amax=min(block.getA(),Amax)
            deviation += block.calcDeviation()
            nbrOfCustomers += block.getNbrOfPassengers()
        ui=self.getUi(booking.getEPT())
        aStar = round(-(-self.constants["c1"]*nbrOfCustomers-2*self.constants["c2"]*deviation + \
                        (self.constants["c6"]+self.constants["c8"]*ui)*I)/ \
                      (2*self.constants["c2"])*nbrOfCustomers)
        lb = 0
        ub = Amax-Rmin
        a = aStar
        if aStar<lb:
            a = lb
        elif aStar>ub:
            a = ub
        for block in schedule:
            block.shiftSchedule(a)


    def calcIncrementalCost(self,schedule,booking,shift):

        bookings=dict()
        #assigning to every booking its pickup and delivery stops:
        for block in schedule:
            for stop in block.stops:
                bookings.setdefault(stop.getBooking(),[]).append(stop)

        duNewBooking = self.disutilityFuncBooking(booking,bookings[booking][0],bookings[booking][1])
        bookings.pop(booking)
        duOthers=0
        for booking in bookings:
            duOthers += self.disutilityFuncBooking(booking,bookings[booking][0],bookings[booking][1]) \
                        -booking.getDisutility()
        duOperator=self.disutilityFuncShift(schedule,booking,shift)
        return duNewBooking + duOthers + duOperator


    def disutilityFuncShift(self,schedule,booking,shift):
        #VCi = C5*z + C6*w + Ui*( C7*z + C8*w)
        #in our case : vc =z(c5-c6)+ui*z*(c7-c8) since change in service time z = - change in vehicle slack time w

        #calculating service time change:
        #
        z=0
        for block in schedule:
            z+=block.calcServiceTime()
        z-=shift.getServiceTime()
        ui=self.getUi(booking.getEPT())
        return z*(self.constants["c5"]-self.constants["c6"])+ui*z*(self.constants["c7"]-self.constants["c8"])


    def disutilityFuncBooking(self, booking, pick_up, delivery):
        #to change
        x = booking.getDPT() - delivery.getST()
        y = delivery.getST() - pick_up.getST() - booking.getDRT()
        dud = self.constants["c1"]*x + self.constants["c2"]*x*x
        dur = self.constants["c3"]*y + self.constants["c4"]*y*y
        return dud + dur


    def getConstant(self,const):
        return self.constants.get(const,0)

    def getUi(self,ept):
        custInSys = 0
        shiftsAvailable = 0
        for booking in self.bookings:
            if ept-self.constants["W1"] <=booking.getEPT() <= ept+self.constants["W2"] or \
                                            ept-self.constants["W1"] <=booking.getLDT() <= ept+self.constants["W2"]:
                custInSys += 1
        for shift in self.shifts:
            if shift.getStart() <= ept+self.constants["W2"] or \
                                    ept-self.constants["W1"] <=shift.getEnd():
                shiftsAvailable += 1

        #carsAvailable !=0 because otherwise the initial algorithm would not proceed in the first place
        return custInSys/shiftsAvailable

    def removePastStops(self,time):
        for car in self.cars:
            car.removePastStops(time)

    def dynamicInsertion(self,time,meals):
        self.meals=meals
        self.removePastStops(time)
        self.createSchedules()


    def getNotInsertedMeals(self):
        return self.mealsNotInserted