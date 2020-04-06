import json
import matplotlib.pyplot as plt
from random import random

#### DATA EXTRACTION ####

with open("data/week2_data.json") as json_data:
    data = json.load(json_data)

latitude={}
longitude={}
listevoiture=[]

for client in data["bookings"]:
    for job in client["jobs"]:
        latitude[job["id"]]=job["latitude"]
        longitude[job["id"]]=job["longitude"]
for voiture in data["shifts"]:
    listevoiture.append(voiture["id"])
    for job in voiture["jobs"]:
        latitude[job["id"]]=job["latitude"]
        longitude[job["id"]]=job["longitude"]

#### PLOT ####

couleur={}
for voiture in listevoiture:
    couleur[voiture]=(random(),random(),random())

with open("results/insertion_v2_week2.json") as json_data:
    resjson = json.load(json_data)

for shift in resjson["shifts"]:
    listex=[]
    listey=[]
    for job in shift["jobs"]:
        listex.append(latitude[job["id"]])
        listey.append(longitude[job["id"]])
    plt.plot(listex,listey,color=couleur[shift["id"]])

plt.title("Insertion v2 week2_data")
plt.xlabel("Latitude")
plt.ylabel("Longitude")
plt.show()