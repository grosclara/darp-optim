from Stop import *
from Block import *

from copy import deepcopy

class Shift:

    def __init__(self, long_id, capacity, max_turnover, depots, travel_time):

        self.long_id = long_id
        self.capacity = capacity
        self.max_turnover = max_turnover
        self.depots = depots
        self.travel_time = travel_time
        self.start = self.depots[0].time_date
        self.end = self.depots[1].time_date

        #self.depot = depot

        self.bookings = []

        self.currentSchedule = []
        self.feasibleSchedules = []

        self.serviceTime = 0


    def setCurrentSchedule(self, schedule):
        self.currentSchedule = schedule
        i = 0
        stop1 = self.currentSchedule[0].getFirstStop()
        dist = self.travel_time[self.depots[0].station, stop1.getNode().station]
        timeDiff = stop1.getST() - self.start
        slack = timeDiff - dist
        self.currentSchedule[0].setPrevSlack(slack)
        while i < len(self.currentSchedule) - 1:
            stop1 = self.currentSchedule[i].getLastStop()
            stop2 = self.currentSchedule[i + 1].getFirstStop()
            timeDiff = stop2.getST() - stop1.getST()
            dist = self.travel_time[stop1.getNode().station, stop2.getNode().station]
            slack = timeDiff - dist
            if slack != 0:
                self.currentSchedule[i].setNextSlack(slack)
                self.currentSchedule[i + 1].setPrevSlack(slack)
                i += 1
            else:
                block = self.currentSchedule[i + 1]
                self.currentSchedule.remove(block)
                self.currentSchedule[i].blockFusion(block)
        stop2 = self.currentSchedule[-1].getLastStop()
        dist = self.travel_time[stop2.getNode().station, self.depots[1].station]
        timeDiff = self.end - stop2.getST()
        slack = timeDiff - dist
        self.currentSchedule[-1].setNextSlack(slack)
        self.serviceTime=0
        for block in self.currentSchedule:
            block.calcUPnDOWN()
            self.serviceTime+=block.calcServiceTime()



    def addIntoSameBlock(self, booking, scheduler):
        """
        Trying to fit the booking into the existing working schedule while
        pickup and delivery happen in the same block
        :param booking:
        :return:
        """

        self.feasibleSchedules = []
        if self.currentSchedule != []:
            # case1 : pickup and delivery are inserted at the end of the working schedule.
            self.case1(booking, scheduler)

            # case 2 : pickup and delivery are consecutive stops in a block
            self.case2(booking)

            # case 3 : pickup in the last block, delivery becomes last stop in schedule
            self.case3(booking)

            # case 4 : pickup and delivery are separated by at least one stop
            self.case4(booking)

            return True

        # case0 : first Block is being created if possible
        self.case0(booking, scheduler)
        # return


    def addIntoDifferentBlocks(self, booking):

        # pickup and delivery are in different blocks
        i = 0
        schedule = deepcopy(self.currentSchedule)
        while i < len(schedule) - 1:
            block = schedule[i]
            initBlockLength = len(block)
            destinationBlockIndex=initBlockLength
            slack = block.getPrevSlack() + block.getNextSlack()
            j = i + 1
            while j < len(schedule):
                destinationBlock = schedule[j]
                slack += destinationBlock.getNextSlack()
                block.blockFusion(destinationBlock)
                schedule.remove(destinationBlock)
                d = destinationBlockIndex + len(destinationBlock)
                for pickupIndex in range(initBlockLength):
                    p=block.getStopAt(pickupIndex)
                    q=block.getStopAt(pickupIndex+1)
                    deltaP = self.travel_time[p.getNode().station, booking.getPickUp().station] + \
                             self.travel_time[booking.getPickUp().station, q.getNode().station] - \
                             self.travel_time[p.getNode().station, q.getNode().station]
                    for deliveryIndex in range(destinationBlockIndex,d-1):
                        g=block.getStopAt(deliveryIndex)
                        h=block.getStopAt(deliveryIndex+1)
                        deltaD = self.travel_time[g.getNode().station, booking.getDropOff().station] + \
                                 self.travel_time[booking.getDropOff().station, h.getNode().station] - \
                                 self.travel_time[g.getNode().station, h.getNode().station]
                        if deltaD+deltaP<=slack:
                            stop1 = Stop(booking.getPickUp(), 0, booking, True)
                            stop2 = Stop(booking.getDropOff(), 1, booking, False)
                            block.insertStop(pickupIndex+1,stop1)
                            block.insertStop(deliveryIndex+1,stop2)
                            if self.verifyInsertionForDifferentTimeBlocks(block,d):
                                self.feasibleSchedules.append(schedule)
                            schedule=deepcopy(self.currentSchedule)
                            block=schedule[i]
                            k=i+1
                            for t in range(j-i):
                                block.blockFusion(schedule[k])
                                schedule.remove(schedule[k])


                destinationBlockIndex+=len(destinationBlock)
                j += 1

            i += 1


    def verifyInsertionForDifferentTimeBlocks(self, block, d):
        """
        Performing the algorithm described in Figure I.2 to
        """
        latestTime=dict()
        r = 0
        feasible = True
        t_rMinus1 = block.getStopAt(r)
        t_rMinus1.setST(t_rMinus1.getST() - block.getPrevSlack())

        Rmin = 0
        Amax = float("inf")
        charge=0
        while r<d and feasible:
            t=block.getStopAt(r)
            t.setST(t_rMinus1.getST()+self.travel_time[t_rMinus1.getNode().station,t.getNode().station])
            Rr=abs(min(t.getST()-t.getET(),0))
            Ar=t.getLT()-t.getST()
            Rmin=max(Rr,Rmin)
            Amax=min(Ar,Amax)
            if t.isPickup():
                charge+=1
                latestTime[t.getBooking()] = t.getST() + t.getBooking().getMRT()
            else:
                if t.getST()>latestTime[t.getBooking()]:
                    feasible= False
                charge-=1
            if Rmin<=Amax and charge<=self.capacity:
                t_rMinus1=t
            else:
                feasible= False
            r +=1
        block.shiftSchedule(Rmin)




        return feasible


    
    def case0(self, booking, scheduler):
        """
        First insertion to the schedule
        """
        # if self.start <= booking.getEPT()
        if self.start + self.travel_time[self.depots[0].station, booking.getPickUp().station] <= booking.getLPT() \
            and (self.start + self.travel_time[self.depots[0].station, booking.getPickUp().station] + booking.getDRT() + self.travel_time[booking.getDropOff().station, self.depots[1].station] ) <= self.end :

            stop1 = Stop(booking.getPickUp(), booking.getDPT(), booking, True)
            stop2 = Stop(booking.getDropOff(), booking.getDPT() + booking.getDRT(), booking, False)

            prevSlack = stop1.getST() - self.start - self.travel_time[self.depots[0].station, booking.getPickUp().station]
            nextSlack = self.end - stop2.getST() - self.travel_time[booking.getDropOff().station, self.depots[1].station] 

            block = Block(stop1, stop2, prevSlack, nextSlack)

            self.feasibleSchedules.append([block])

    def case1(self, booking, scheduler):
        """
        Following logic of algorithm case 1
        """
        # verify charge

        schedule = deepcopy(self.currentSchedule)
        block = schedule[-1] #Last work block
        lastNode = block.getLastStop().getNode() # Last node of the last work block of the whole shift schedule

        # Schedule already optimized ????
        if block.getEnd() + self.travel_time[lastNode.station, booking.getPickUp().station] < booking.getLPT() and \
            block.getEnd() + self.travel_time[lastNode.station, booking.getPickUp().station] + booking.getDRT() \
                + self.travel_time[booking.getDropOff().station, self.depots[1].station] < self.end :

            tpu = block.getEnd() + self.travel_time[lastNode.station, booking.getPickUp().station] #time puck up
            td = tpu + booking.getDRT() #time drop off
            # ddt or dpt
            shift = 0
            w = 0
            if td <= booking.getLDT():
                tpu = booking.getLDT() - booking.getDRT()
                td = booking.getLDT()
                w = tpu - block.getEnd() - self.travel_time[lastNode.station, booking.getPickUp().station]
                if scheduler.getConstant("c2") != 0:
                    shift = max((scheduler.getConstant("c6") +
                                 scheduler.getConstant("c8") * scheduler.getUi(
                                     booking.getEPT())) / 2 * scheduler.getConstant("c2"), 0)
                    shift = min(shift, w, booking.getDeviation())
                    tpu -= shift
                    td -= shift

                else:
                    if scheduler.getConstant("c1") < scheduler.getConstant("c6") \
                            + scheduler.getConstant("c8") * scheduler.getUi(booking.getEPT()):
                        w = max(0, w - booking.getDeviation())
                        tpu = block.getEnd() + self.travel_time[lastNode.station, booking.getPickUp().station] + w
                        td = tpu + booking.getDRT()

            else:
                shift = tpu - booking.getLDT()
                if shift > block.getLastStop().getBUP():
                    return False
                else:
                    td = booking.getLDT()
                    tpu = td - booking.getDRT()
                    ps = -shift
                    block.shiftSchedule(ps)
                    # for stop in block:
                    #     stop.shiftST(ps)

            stop1 = Stop(booking.getPickUp(), tpu, booking, True)
            stop2 = Stop(booking.getDropOff(), td, booking, False)
            if w != 0:  # after the current last stop there will be slack time -> create new block #depots 0 ou 1 ??
                bb = Block(stop1, stop2, w, self.end - stop2.getST() - self.travel_time[self.depots[1].station, stop2.getNode().station])
                block.setNextSlack(w)
                schedule.append(bb)
                self.feasibleSchedules.append(schedule)
                return True

            if block.getNbrOfPassengers() < self.capacity:
                # the 2 stops become the last 2 stops in the block and the schedule
                nextSlack = block.getNextSlack()

                block.addLastStop(stop1)
                block.addLastStop(stop2)

    def case2(self, booking):
        """
        """
        i = 0
        while i < len(self.currentSchedule):
            schedule = deepcopy(self.currentSchedule)
            block = schedule[i]
            for j in range(len(block) - 1):
                p = block.getStopAt(j)
                q = block.getStopAt(j + 1)
                # checking charge-feasibility before launching the algorithm
                if block.getChargeBefore(j) < self.capacity:  # and self.case2Algo(p,q,meal,j):
                    
                    deltaP = self.travel_time[p.getNode().station, booking.getPickUp().station] + booking.getDRT() + \
                             self.travel_time[booking.getDropOff().station, q.getNode().station] - \
                             self.travel_time[p.getNode().station, q.getNode().station]   

                    if deltaP <= p.getBUP() + q.getADOWN():
                        feasible = True
                        tpu = 0
                        td = 0
                        ps = 0
                        ds = 0
                        gt = 0
                        et = 0
                        lt = 0
                        shift = 0
                        if deltaP > q.getADOWN():
                            ds = q.getADOWN()
                            ps = q.getADOWN() - deltaP
                            tpu = p.getST() + ps + self.travel_time[p.getNode().station, booking.getPickUp().station]
                            td = tpu + booking.getDRT()
                        else:
                            ps = 0
                            ds = deltaP
                            tpu = p.getST() + self.travel_time[p.getNode().station, booking.getPickUp().station]
                            td = tpu + booking.getDRT()
                        # ddt, so : (be careful, dpt !!!!)
                        gt = td
                        et = booking.getEDT()
                        lt = booking.getLDT()
                        if gt < et:
                            shift = et - gt
                            if shift > (q.getADOWN() - ds) or shift > p.getBDOWN() - ps:
                                feasible = False
                            else:
                                tpu += shift
                                td += shift
                                ds += shift
                                ps += shift

                        elif gt > lt:
                            shift = gt - lt
                            if shift > (q.getAUP() + ds) or shift > (p.getBUP() + ps):
                                feasible = False
                            else:
                                tpu -= shift
                                td -= shift
                                ds -= shift
                                ps -= shift

                        if feasible:
                            stop1 = Stop(booking.getPickUp(), tpu, booking, True)
                            stop2 = Stop(booking.getDropOff(), td, booking, False)
                            # inserting the 2 stops between stop p and q
                            block.insertStop(j + 1, stop1)
                            block.insertStop(j + 2, stop2)
                            # shifting block schedule:
                            block.shiftScheduleBefore(stop1, ps)
                            block.shiftScheduleAfter(stop2, ds)
                            self.feasibleSchedules.append(schedule)

                            schedule = deepcopy(self.currentSchedule)
                            block = schedule[i]
            i += 1

    def case3and4(self, p, q, r, booking):
        """
        Common code of case 3 and 4
        """
        deltaP = self.travel_time[p.getNode().station, booking.getPickUp().station] + \
                 self.travel_time[booking.getPickUp().station, q.getNode().station] - \
                 self.travel_time[p.getNode().station, q.getNode().station]
        ps = 0
        ms = 0
        ds = 0
        tpu = 0
        td = 0
        feasible = False
        if deltaP <= p.getBUP() + q.getADOWN():
            feasible = True
            if deltaP > p.getBUP():
                ps = -p.getBUP()
                ms = deltaP - p.getBUP()
                tpu = p.getST() - p.getBUP() + self.travel_time[p.getNode().station, booking.getPickUp().station]
                ds = ms
            else:
                ps = -deltaP
                tpu = p.getST() - deltaP + self.travel_time[p.getNode().station, booking.getPickUp().station]
            td = r.getST() + ms + self.travel_time[r.getNode().station, booking.getDropOff().station]
        return feasible, deltaP, ps, ms, ds, tpu, td

    def case3(self, booking):
        """
        Algo of case3
        """
        schedule = deepcopy(self.currentSchedule)
        block = schedule[-1]
        r = block.getLastStop()
        for i in range(len(block) - 2):
            p = block.getStopAt(i)
            q = block.getStopAt(i + 1)
            feasible, deltaP, ps, ms, ds, tpu, td = self.case3and4(p, q, r, booking)
            if feasible:
                # ddt, so :
                gt = td
                et = booking.getEDT()
                lt = booking.getLDT()
                if gt > lt:
                    shift = gt - lt
                    if shift > (p.getBUP() + ps) or shift > (q.getAUP() + ms):
                        feasible = False
                    else:
                        tpu -= shift
                        td -= shift
                        ps -= shift
                        ms -= shift
                elif gt < et:
                    shift = et - gt
                    if shift > (p.getBDOWN() - ps) or shift > (q.getADOWN() - ms):
                        feasible = False
                    else:
                        tpu += shift
                        td += shift
                        ps += shift
                        ms += shift

                if feasible:
                    stop1 = Stop(booking.getPickUp(), tpu, booking, True)
                    stop2 = Stop(booking.getDropOff(), td, booking, False)
                    block.insertStop(i + 1, stop1)
                    block.addLastStop(stop2)
                    block.shiftScheduleBetween(stop1, stop2, ms)
                    block.shiftScheduleBefore(stop1, ps)
                    if block.respectCharge(self.capacity):
                        self.feasibleSchedules.append(schedule)
                    schedule = deepcopy(self.currentSchedule)
                    block = schedule[-1]

    def case4(self, booking):
        """
        Algo of case 4
        """
        schedule = deepcopy(self.currentSchedule)
        for i in range(len(schedule)):
            block = schedule[i]
            for j in range(len(block) - 2):
                p = block.getStopAt(j)
                q = block.getStopAt(j + 1)
                for k in range(j + 1, len(block) - 2):
                    r = block.getStopAt(k)
                    feasible, deltaP, ps, ms, ds, tpu, td = self.case3and4(p, q, r, booking)
                    if feasible:
                        s = block.getStopAt(k + 1)
                        deltaD = self.travel_time[r.getNode().station, booking.getDropOff().station] + \
                                 self.travel_time[booking.getDropOff().station, s.getNode().station] - \
                                 self.travel_time[r.getNode().station, s.getNode().station]
                        if deltaD <= (r.getBUP() + s.getADOWN()) or (deltaP + deltaD) <= (s.getADOWN()
                                                                                              + p.getBUP()):
                            if (deltaD + ds) > s.getADOWN():
                                ds = s.getADOWN()
                                ms = -(deltaD - s.getADOWN())
                                ps += ms
                                tpu += ms
                                td += ms
                            else:
                                ds += deltaD
                            # ddt, so:
                            gt = td
                            et = booking.getEDT()
                            lt = booking.getLDT()
                            if gt < et:
                                shift = et - gt
                                if shift > (q.getADOWN() - ms) or shift > (p.getBDOWN() - ps) or shift > (
                                            s.getADOWN() - ds):
                                    feasible = False
                                else:
                                    td += shift
                                    tpu += shift
                                    ms += shift
                                    ps += shift
                                    ds += shift
                            elif gt > lt:
                                shift = gt - lt
                                if shift > (s.getAUP() + ds) or shift > (p.getBUP() + ps) or shift > (
                                            r.getBUP() + ms):
                                    feasible = False
                                else:
                                    td -= shift
                                    tpu -= shift
                                    ms -= shift
                                    ps -= shift
                                    ds -= shift

                            if feasible:
                                stop1 = Stop(booking.getPickUp(), tpu, booking, True)
                                stop2 = Stop(booking.getDropOff(), td, booking, False)
                                block.insertStop(j + 1, stop1)
                                block.insertStop(k + 2, stop2)
                                block.shiftScheduleBefore(stop1, ps)
                                block.shiftScheduleAfter(stop2, ds)
                                block.shiftScheduleBetween(stop1, stop2, ms)
                                if block.respectCharge(self.capacity):
                                    self.feasibleSchedules.append(schedule)
                                schedule = deepcopy(self.currentSchedule)
                                block = schedule[i]
                                

    def removePastStops(self,time):
        i=0
        while i<len(self.currentSchedule) and self.currentSchedule[i].getStart()<time:
            self.currentSchedule[i].removePastStops(time)
            if len(self.currentSchedule[i])==0:
                self.currentSchedule.remove(self.currentSchedule[i])
                i-=1
            i+=1
    
    def __repr__(self):
        return str(self.long_id)