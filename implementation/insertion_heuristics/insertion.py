import json
import pandas
#extraction des donnes
with open("week_data.json") as json_data:
    data = json.load(json_data)

time_data = pandas.read_csv("travel_times.csv", sep=';')

nb_stations = len(time_data)
time = {}

for i in range(nb_stations):
    for j in range(nb_stations):
        time["s"+str(i), "s"+str(j)] = int(time_data["s{}".format(i)][j])
#creation de dictionnaire pour utiliser les données plus facilement (avoir accès à toutes les données uniquement avec les id)
station={}
prix={}
charge={}
duree={}
clients={}
debut={}
fin={}

depose={}
prise={}
dureemax={}

capacite={}
salairemax={}

for client in data["bookings"]:
    dureemax[client["id"]]=client["maximumDuration"]
    for job in client["jobs"]:
        station[job["id"]]=job["station"]
        duree[job["id"]]=job["duration"]
        clients[job["id"]]=client["id"]
        debut[job["id"]]=job["timeWindowBeginDate"]
        fin[job["id"]]=job["timeWindowEndDate"]
        if job["type"]=="PickUpJob":
            prix[job["id"]]=client["price"]
            charge[job["id"]]=client["passengers"]
            prise[client["id"]]=job["id"]
        else:
            prix[job["id"]]=0
            charge[job["id"]]=-client["passengers"]
            depose[client["id"]]=job["id"]
for voiture in data["shifts"]:
    capacite[voiture["id"]]=voiture["capacity"]
    salairemax[voiture["id"]]=voiture["maximumTurnover"]
    prise[voiture["id"]]=voiture["jobs"][0]["id"]
    depose[voiture["id"]]=voiture["jobs"][1]["id"]
    for job in voiture["jobs"]:
        debut[job["id"]]=voiture["jobs"][0]["timeDate"]
        fin[job["id"]]=voiture["jobs"][1]["timeDate"]
        duree[job["id"]]=0
        station[job["id"]]="s0"




#notation utilisée
#voiture correspond à l'id associé à chaaque voiture'
#course correspond à l'ensemble des course qu'une voiture verifie


def verifie(course,voiture):
    #renvoie true si un ensemble de course est realisable par une voiture, false sinon
    for k in range(1, len(course) - 1):
        if  course[k][1]<debut[course[k][0]] or course[k][1]>fin[course[k][0]] :
            #verifie les contraintes de borne de temps pour chaque job
            return(False)
        for i in range(k+1, len(course) - 1):
            if course[i][0]==depose[clients[course[k][0]]]:
                if course[i][1]-course[k][1]>dureemax[clients[course[k][0]]]:
                    return(False)
                    #verifie les contraintes de durée maximum des clients
    salaire=0
    charg=0
    chargemax=0
    for k in range(1, len(course) - 1):
            salaire+=prix[course[k][0]]
            charg+=charge[course[k][0]]
            if charg>chargemax:
                chargemax=charg
    if chargemax>capacite[voiture] or salaire>salairemax[voiture]:
        return(False)
        #verifie les contraintes de charge et salaire max pour la voiture
    for x in pause(course):
        if x<0:
            return(False)
            #verifie que les trajets sont fait dans des temps réalisables
    return(True)

def cout(course):
    #calcule le cout lié à un ensemble de course (un seul vehicule)
    cout=0
    for k in range(len(course) - 1):
        cout+=time[(station[course[k][0]], station[course[k + 1][0]])]
    return(cout)

def pause(course):
    #renvoie la liste des temps de pause intermediare pour un ensemble de course. Listepause[k] est la pause entre le keme et le k+1eme element de course
    listepause=[]
    for k in range(len(course) - 1):
        listepause.append(course[k + 1][1] - time[(station[course[k][0]], station[course[k + 1][0]])] - duree[course[k][0]] - course[k][1])
    return(listepause)


def insertclient(client,voiture):
    #renvoie la liste de toutes les ensemble de courses possible en inserant client dans  voiture
    listeprecedentinsertion=[[],[]]
    i=0
    for job in [prise,depose]:
        for k in range(1,len(res[voiture])):
            #print(res[voiture][k][1])
            if res[voiture][k][1]>=debut[job[client]]:
                listeprecedentinsertion[i].append(k-1)
            if res[voiture][k][1]>fin[job[client]]:
                break
        i+=1
    listecandidat=[]

    for i in listeprecedentinsertion[0]:
        for j in listeprecedentinsertion[1]:
            candidat=[]
            for x in res[voiture]:
                candidat.append(x[:])

            listepause=pause(candidat)
            retard=time[(station[candidat[i][0]],station[prise[client]])]+time[(station[prise[client]],station[candidat[i+1][0]])]-time[(station[candidat[i][0]],station[candidat[i+1][0]])]+duree[prise[client]]
            candidat=candidat[:i+1]+[[prise[client],max(debut[prise[client]],candidat[i][1]+time[(station[candidat[i][0]],station[prise[client]])]+duree[candidat[i][0]])]]+candidat[i+1:]


            for k in range(i+2,len(candidat)-1):
                #print(retard,listepause[k-1])
                retard=max(0,retard-listepause[k-1])

                candidat[k][1]+=retard

            listepause=pause(candidat)
            retard=time[(station[candidat[j+1][0]],station[depose[client]])]+time[(station[depose[client]],station[candidat[j+2][0]])]-time[(station[candidat[j+1][0]],station[candidat[j+2][0]])]+duree[depose[client]]

            candidat=candidat[:j+2]+[[depose[client],max(debut[depose[client]],candidat[j+1][1]+time[(station[candidat[j+1][0]],station[depose[client]])]+duree[candidat[j+1][0]])]]+candidat[j+2:]

            for k in range(j+3,len(candidat)-1):
                #print(retard,listepause[k-1])
                retard=max(0,retard-listepause[k-1])

                candidat[k][1]+=retard

            if verifie(candidat,voiture):
                listecandidat.append([cout(candidat),candidat])
    return(listecandidat)

def insertclientoptimal(client,voiture):
    #trouve la façon optimal d'inserer  client dans voiture
    listecandidat=insertclient(client,voiture)

    if len(listecandidat)>0:
        best_course=min(listecandidat)
        return(best_course)
    else:
        return None

# on insere les clients par ordre croissant d'arrivée
res={}
for voiture in capacite.keys():
    res[voiture]=[[prise[voiture],debut[prise[voiture]]],[depose[voiture],fin[depose[voiture]]]]

listeclient=[]
clientrejete=[]

for client in dureemax.keys():
    listeclient.append((debut[depose[client]],client))
listeclient.sort()

for client in listeclient:
    listecandidat=[]
    for voiture in salairemax.keys():
        course=insertclientoptimal(client[1], voiture)
        if course!=None:
            listecandidat.append([course[0] - cout(res[voiture]), course[1], voiture])
    if len(listecandidat)>0:
        best=min(listecandidat)
        res[best[2]]=best[1]
    else:
        l=clientrejete.append(client)


#ecriture du json
nb_assigned_bookings=len(listeclient)-len(clientrejete)
shifts=[]
route_cost=0

for voiture in res.keys():
    route_cost+=cout(res[voiture])
    dic={}
    dic["id"]=voiture
    jobs=[]
    for job in res[voiture]:
        jobs.append({"id":job[0],"time":job[1]})
    dic["jobs"]=jobs
    shifts.append(dic)


resjson={"nb_assigned_bookings":nb_assigned_bookings,"route_cost":route_cost,"shifts":shifts}
with open('results_week_insertion.json', 'w', encoding='utf-8') as f:
    json.dump(resjson, f, indent=4)


