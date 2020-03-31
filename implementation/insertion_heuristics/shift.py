class Shift:
    def __init__(self, long_id, capacity, max_turnover, jobs):
        self.long_id = long_id
        self.capacity = capacity
        self.max_turnover = max_turnover
        self.jobs = jobs

    def __repr__(self):
        return str(self.long_id)