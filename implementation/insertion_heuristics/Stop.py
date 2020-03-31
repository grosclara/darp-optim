class Stop:

    def __init__(self, node, time, booking, pick_up):

        self.node = node
        self.st = time  # scheduled time
        self.booking = booking
        self.pick_up = pick_up

        self.bup = 0  # max time preceding stops can be advanced  [0..r]
        self.bdown = 0  # max time preceding stops can be delayed  [0..r]
        self.aup = 0  # max time following stops can be advanced  [r..d]
        self.adown = 0  # max time following stops can be delayed  [r..d]
        #
        # self.r=abs(min(self.st-self.getET(),0))
        # self.a=self.getLT()-self.st


    def getST(self):
        return self.st

    def getDT(self):
        if self.pick_up:
            return 0
        else:
            return self.booking.getDPT()

    def getR(self):
        return abs(min(self.st-self.getET(),0))

    def getA(self):
        return self.getLT()-self.st


    def getET(self):
        if self.pick_up:
            return self.booking.getEPT()
        else:
            return self.booking.getEDT()

    def getLT(self):
        if self.pick_up:
            return self.booking.getLPT()
        else:
            return self.booking.getLDT()

    def getNode(self):
        return self.node

    def getBUP(self):
        return self.bup

    def getBDOWN(self):
        return self.bdown

    def getAUP(self):
        return self.aup

    def getADOWN(self):
        return self.adown

    def setST(self,newST):
        self.st=newST

    def setBUP(self,newBUP):
        self.bup=newBUP

    def setBDOWN(self,newBDOWN):
        self.bdown=newBDOWN

    def setAUP(self,newAUP):
        self.aup=newAUP

    def setADOWN(self,newADOWN):
        self.adown=newADOWN

    def getBooking(self):
        return self.booking

    def shiftST(self,shift):
        self.st += shift

    def isPickup(self):
        return self.pick_up


    def __str__(self):
        txt="Noeud : {0}, Coords : {1} , time : {2} , ".format(self.node.index,(self.node.i,self.node.j),self.st)
        txt+="BUP : {0} , BDOWN : {1} , AUP : {2} , ADOWN : {3}\n".format(
            self.bup,self.bdown,self.aup,self.adown)
        return txt