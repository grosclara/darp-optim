import json

from extract_data import nb_bookings, parameters, node_to_station, bookings, shifts

travel_time = parameters["time_table_dict"]

with open("exact_solving/results/results_day.json") as json_data:
     data_dict = json.load(json_data)

nb_assigned_bookings = 0
route_cost = 0

res={}
for var in data_dict["Solution"][1]["Variable"].keys():

    if var[0]=="x":
        lvar=var[2:len(var)-1].split(",")
        lvar = list(map(int, lvar))

        route_cost += travel_time[(node_to_station[lvar[0]],node_to_station[lvar[1]])]

        if lvar[2] not in res.keys():
                res[lvar[2]]=[]
        try :
            time = data_dict["Solution"][1]["Variable"]["u["+str(lvar[0])+","+str(lvar[2])+"]"]["Value"]
        except :
            time = 0

        if lvar[0] != 0 and lvar[0] != 2*nb_bookings+1:
            
            if lvar[0] <= nb_bookings:
                nb_assigned_bookings += 1


            if lvar[0] <= nb_bookings :
                job_id = bookings[lvar[0]-1].jobs[0].long_id
            else : 
                job_id = bookings[lvar[0]-nb_bookings-1].jobs[1].long_id
                        
        elif lvar[0] == 0 :
            for shift in shifts :
                if shift.long_id == lvar[2] :
                    job_id = shift.jobs[0].long_id

        res[lvar[2]].append({"id":job_id, "time":time})


res2=[]
for k in res.keys():
    res2.append({"id":k,"jobs":res[k]})


res3={"nb_assigned_bookings": nb_assigned_bookings, "route_cost":route_cost, "shifts": res2}

with open('exact_solving/results/results_day_good_format.json', 'w', encoding='utf-8') as f:
   json.dump(res3, f, indent=4)


