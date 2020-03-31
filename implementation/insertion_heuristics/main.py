from Darp import *
from Shift import *
from Booking import *

from insertion_extract_data import bookings, shifts

if __name__=="__main__":

    darp = Darp(bookings = bookings, shifts = shifts)
    darp.createSchedules()