import json
import pandas

############# Data extraction #############
with open("data/week_data.json") as json_data:
    data = json.load(json_data)

time_data = pandas.read_csv("data/travel_times.csv", sep=';')

nb_stations = len(time_data)

time = {}
for i in range(nb_stations):
    for j in range(nb_stations):
        time["s"+str(i), "s"+str(j)] = int(time_data["s{}".format(j)][i])

station = {}
price = {}
load_dict = {}
duration = {}
clients = {}
start = {}
end = {}

pick_up = {}
drop_off = {}
max_ride_time = {}

capacity = {}
max_turnover = {}

for client in data["bookings"]:

    max_ride_time[client["id"]] = client["maximumDuration"]

    for job in client["jobs"] :
        station[job["id"]] = job["station"]
        duration[job["id"]] = job["duration"]
        clients[job["id"]] = client["id"]
        start[job["id"]] = job["timeWindowBeginDate"]
        end[job["id"]] = job["timeWindowEndDate"]

        if job["type"] == "PickUpJob" :
            price[job["id"]] = client["price"]
            load_dict[job["id"]] = client["passengers"]
            pick_up[client["id"]] = job["id"]

        else :
            price[job["id"]] = 0
            load_dict[job["id"]] = -client["passengers"]
            drop_off[client["id"]] = job["id"]

for shift in data["shifts"] :

    capacity[shift["id"]] = shift["capacity"]
    max_turnover[shift["id"]] = shift["maximumTurnover"]
    pick_up[shift["id"]] = shift["jobs"][0]["id"]
    drop_off[shift["id"]] = shift["jobs"][1]["id"]

    for job in shift["jobs"] :
        start[job["id"]] = shift["jobs"][0]["timeDate"]
        end[job["id"]] = shift["jobs"][1]["timeDate"]
        duration[job["id"]] = 0
        station[job["id"]] = "s0"


def check_constraints(schedule, shift) :
    """
        Return True if a set of bookings is feasible by a shift, False otherwise
    """
    for k in range(1, len(schedule)-1) :

        # Check time window constraint
        if schedule[k][1] < start[schedule[k][0]] or schedule[k][1] > end[schedule[k][0]] :
            return False

        # Check maximum ride time constraint
        for i in range(k+1, len(schedule)-1) :
            if schedule[i][0] == drop_off[clients[schedule[k][0]]]:
                if schedule[i][1] - schedule[k][1] > max_ride_time[clients[schedule[k][0]]]:
                    return False

    # Check max load and turnover constraintes for shift
    turnover = 0
    load = 0
    max_load = 0
    for k in range(1, len(schedule)-1) :
            turnover += price[schedule[k][0]]
            load += load_dict[schedule[k][0]]
            if load > max_load :
                max_load = load

    if max_load > capacity[shift] or turnover > max_turnover[shift] :
        return False

    # Check that rides are done in a feasible time
    for x in compute_slack_periods(schedule) :
        if x < 0 :
            return False

    return True

def cost(schedule) :
    """
        Compute the cost of a schedule (set of bookings)
    """
    cost = 0
    for k in range(len(schedule) - 1) :
        cost += time[(station[schedule[k][0]], station[schedule[k + 1][0]])]
    return cost

def global_cost(shift_schedules) :
    global_cost = 0
    for schedule in shift_schedules.values() :
        global_cost += cost(schedule)
    return global_cost

def compute_slack_periods(schedule):
    """
        Return the list of slack periods for a set of bookings.
        slack[k] is the slack time between the k-th and de k+1-th stops 
    """
    slack = []
    for k in range(len(schedule) - 1):
        slack.append(schedule[k + 1][1] - time[(station[schedule[k][0]], station[schedule[k + 1][0]])] - duration[schedule[k][0]] - schedule[k][1])
    return slack


def insert_client(client, shift, schedule):
    """
        Returns the list of all possible insertions of client in shift
    """
    # List of jobs index after which it is in theory feasible to insert the pick up/drop off of client
    previous_insertions = [[],[]]
    i=0

    # You can only insert a job after a course if the time of the course is within the time interval of the job or just before it.
    for job in [pick_up, drop_off] :
        # Compare the job time window with the stops already planned (apart from the start depot)
        for k in range(1, len(schedule)) :
            if schedule[k][1] >= start[job[client]] :
                previous_insertions[i].append(k-1)
            if schedule[k][1] > end[job[client]] :
                break
        i+=1

    candidates = []

    for i in previous_insertions[0] :
        for j in previous_insertions[1] :
            candidat = []
            for x in schedule :
                # Creation of a schedule copy not to modify it
                candidat.append(x[:])

            slack = compute_slack_periods(candidat)
            # Detour delay to pick up the client
            delay = time[(station[candidat[i][0]], station[pick_up[client]])] \
                + time[(station[pick_up[client]],station[candidat[i+1][0]])] \
                - time[(station[candidat[i][0]],station[candidat[i+1][0]])] \
                + duration[pick_up[client]]
            # Insertion of the pick up before stop i
            candidat = candidat[:i+1] \
                + [[pick_up[client], \
                     max(start[pick_up[client]], \
                         candidat[i][1] + time[(station[candidat[i][0]], station[pick_up[client]])] \
                + duration[candidat[i][0]])]]+candidat[i+1:]

            for k in range(i+2,len(candidat)-1):
                # Stops after this insertion are delayed
                # The delay is eventually mitigated if the shift had slack periods. 
                delay = max(0, delay - slack[k-1])
                candidat[k][1] += delay

            slack = compute_slack_periods(candidat)
            # Detour delay to drop off the client
            delay = time[(station[candidat[j+1][0]],station[drop_off[client]])] \
                + time[(station[drop_off[client]], station[candidat[j+2][0]])] \
                - time[(station[candidat[j+1][0]], station[candidat[j+2][0]])] \
                + duration[drop_off[client]]
            # Insertion of drop off after the stop j+1 (indexes are shifted because of the pick up insertion)
            candidat = candidat[:j+2] + \
                [[drop_off[client], \
                    max(start[drop_off[client]], \
                        candidat[j+1][1] + time[(station[candidat[j+1][0]], station[drop_off[client]])] \
                + duration[candidat[j+1][0]])]] + candidat[j+2:]

            for k in range(j+3,len(candidat)-1):
                delay = max(0,delay - slack[k-1])
                candidat[k][1] += delay
            
            if check_constraints(schedule = candidat, shift = shift):
                candidates.append(candidat)

    return(candidates)


def insert_optimal_client(client, shift, schedule):
    """
        Returns the cost and the optimal way to insert client in shift
    """

    candidates = insert_client(client = client, shift = shift, schedule = schedule)

    if len(candidates) > 0 :
        cost_candidates = []
        for candidate in candidates :
            cost_candidate = cost(candidate)
            cost_candidates.append([cost_candidate, candidate])
        best_candidate = min(cost_candidates)
        return(best_candidate)
    else:
        return None


def json_writing(shift_schedules, unassigned_clients) :
    # Json writing
    nb_assigned_bookings = len(sorted_clients) - len(unassigned_clients)
    shifts = []
    route_cost = 0

    for shift in shift_schedules.keys():
        route_cost += cost(shift_schedules[shift])
        dic = {}
        dic["id"] = shift
        jobs = []
        for job in shift_schedules[shift]:
            jobs.append({"id":job[0],"time":job[1]})
        dic["jobs"]=jobs
        shifts.append(dic)

    resjson={"nb_assigned_bookings":nb_assigned_bookings, "route_cost":route_cost, "shifts":shifts}
    with open('heuristics/results/results_week_insertion.json', 'w', encoding='utf-8') as f:
        json.dump(resjson, f, indent=4)



 # shift_schedules[shift] represents the set of stops in the schedule of a shift
shift_schedules = {}
for shift in capacity.keys():
    shift_schedules[shift]=[[pick_up[shift],start[pick_up[shift]]],[drop_off[shift],end[drop_off[shift]]]]

unassigned_clients = []

# Sort each booking (client) according to their earliest drop off lower bound time window
sorted_clients = []
for client in max_ride_time.keys():
    sorted_clients.append((start[drop_off[client]],client))
sorted_clients.sort()

for client in sorted_clients:

    feasible_insertions = []

    for shift in max_turnover.keys():
        # Find optimal insertion of client in shift
        course = insert_optimal_client(client = client[1], shift = shift, schedule = shift_schedules[shift])
        if course != None:
            feasible_insertions.append([course[0] - cost(shift_schedules[shift]), course[1], shift])

    # Check whether at least an insertion in whatever shift is possible
    if len(feasible_insertions) > 0:
        optimal_insertion = min(feasible_insertions)
        shift_schedules[optimal_insertion[2]] = optimal_insertion[1]
    else:
        l = unassigned_clients.append(client)
    
#json_writing(shift_schedules = shift_schedules, unassigned_clients = unassigned_clients)


