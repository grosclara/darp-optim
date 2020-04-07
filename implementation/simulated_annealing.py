import json
import pandas
from random import randint,random
from numpy import exp,log
import matplotlib.pyplot as plt
import time as clock

#extraction des donnes
with open("data/evaluation_data.json") as json_data:
    data = json.load(json_data)

time_data = pandas.read_csv("data/travel_times.csv", sep=';')

nb_stations = len(time_data)
time = {}

for i in range(nb_stations):
    for j in range(nb_stations):
        time["s"+str(i), "s"+str(j)] = int(time_data["s{}".format(j)][i])
#creation de dictionnaire pour utiliser les données plus facilement (avoir accès à toutes les données uniquement avec les id)
station={}
prix={}
charge={}
duree={}
clients={}
debut={}
fin={}
latitude={}
longitude={}

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
        latitude[job["id"]]=job["latitude"]
        longitude[job["id"]]=job["longitude"]
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
        latitude[job["id"]]=job["latitude"]
        longitude[job["id"]]=job["longitude"]
        debut[job["id"]]=voiture["jobs"][0]["timeDate"]
        fin[job["id"]]=voiture["jobs"][1]["timeDate"]
        duree[job["id"]]=0
        station[job["id"]]="s0"




def calcultemps(liste):
    res=[debut[liste[0]]]
    for k in range(1,len(liste)-1):
        res.append(max(debut[liste[k]],res[-1]+time[(station[liste[k-1]],station[liste[k]])]+duree[liste[k-1]]))
    res.append(fin[liste[-1]])
    return(res)

def verifie(listeclient, voiture):
    listetemps=calcultemps(listeclient)
    for k in range(1, len(listeclient) - 1):
        if  listetemps[k]<debut[listeclient[k]] or listetemps[k]>fin[listeclient[k]] :
            #verifie les contraintes de borne de temps pour chaque job
            return(False)
        for i in range(k+1, len(listeclient) - 1):
            if listeclient[i]==depose[clients[listeclient[k]]]:
                if listetemps[i]-listetemps[k]>dureemax[clients[listeclient[k]]]:
                    return(False)
                    #verifie les contraintes de durée maximum des clients
    salaire=0
    charg=0
    chargemax=0
    for k in range(1, len(listeclient) - 1):
            salaire+=prix[listeclient[k]]
            charg+=charge[listeclient[k]]
            if charg>chargemax:
                chargemax=charg
    if chargemax>capacite[voiture] or salaire>salairemax[voiture]:
        return(False)
        #verifie les contraintes de charge et salaire max pour la voiture
    if len(listetemps)>2:
        if listetemps[-1]-listetemps[-2]<time[(station[listeclient[-2]],station[listeclient[-1]])]+duree[listeclient[-2]] or listetemps[-1] < listetemps[-2]:
            return(False)

    return(True)


def insertclient(client, voiture, listeclient):
    emploi_du_temps=calcultemps(listeclient)
    listeprecedentinsertion=[[],[]]#liste des indice des courses après les quelles il est en théorie possible d'inserer la prise/depose du client
    i=0
    #on ne peut inserer un job après une course que si l'heure de la course se trouve dans l'intervalle de temps du job ou juste avant
    for job in [prise,depose]:
        for k in range(1,len(emploi_du_temps)):
            if emploi_du_temps[k]>=debut[job[client]]:
                listeprecedentinsertion[i].append(k-1)
            if emploi_du_temps[k]>fin[job[client]]:
                break
        i+=1
    listecandidat=[]

    for i in listeprecedentinsertion[0]:
        for j in listeprecedentinsertion[1]:
            if j>=i:
                candidat=listeclient[:]
                candidat=candidat[:i+1]+[prise[client]]+candidat[i+1:]
                candidat=candidat[:j+2]+[depose[client]]+candidat[j+2:]
                if verifie(candidat,voiture):
                    listecandidat.append(candidat)
    return(listecandidat)

def cout(listeclient):
    #calcule le cout lié à un emploi du temps (un seul vehicule)
    somme=0
    for k in range(len(listeclient) - 1):
        somme+=time[(station[listeclient[k]], station[listeclient[k + 1]])]
    return(somme)

def cout_total(affectation):
    somme=0
    for emploi_du_temps in affectation.values():
        somme+=cout(emploi_du_temps)
    return(somme)

listeclient=[]
for client in dureemax.keys():
    listeclient.append(client)



def listeclientservi(affectation):
    res=[]
    for emploi_du_temps in affectation.values():
        for k in range(1,len(emploi_du_temps)-1):
            if clients[emploi_du_temps[k]] not in res:
                res.append(clients[emploi_du_temps[k]])
    return(res)

def monformat2json(affectation):
    nb_assigned_bookings=len(listeclientservi(affectation))
    shifts=[]
    route_cost=cout_total(affectation)

    for voiture in affectation.keys():
        dic={}
        dic["id"]=voiture
        jobs=[]
        listeclient=affectation[voiture]
        listetemps=calcultemps(listeclient)
        for k in range(len(listeclient)):

            jobs.append({"id":listeclient[k],"time":listetemps[k]})
        dic["jobs"]=jobs
        shifts.append(dic)
    resjson={"nb_assigned_bookings":nb_assigned_bookings,"route_cost":route_cost,"shifts":shifts}
    return(resjson)

def json2monformat(resjson):
    affectation={}
    for shift in resjson["shifts"]:
        emploi=[]
        for job in shift["jobs"]:
            emploi.append(job["id"])
        affectation[shift["id"]]=emploi
    return(affectation)


def fluctuation1(affectation):
    m=randint(0,len(listeclient)-1)
    client=listeclient[m]
    listevoiture=[voiture for voiture in affectation.keys()]
    indicevoiture=-1
    if client in listeclientservi(affectation):
        arret=False
        for k in range(len(listevoiture)):
            for i in range(1,len(affectation[listevoiture[k]])-1):
                if clients[affectation[listevoiture[k]][i]]==client:
                    indiceprise=i
                    indicevoiture=k
                    indicedepose=None
                    for j in range(i+1,len(affectation[listevoiture[k]])-1):
                        if clients[affectation[listevoiture[k]][j]]==client:
                            indicedepose=j
                            break
                    arret=True
                    break
            if arret:
                break
        voitureclient=listevoiture.pop(indicevoiture)
    listecandidat=[]
    for voiture in listevoiture:
        candidatvoiturek=insertclient(client,voiture,affectation[voiture])
        for candidat in candidatvoiturek:
            listecandidat.append([candidat,voiture])
    if len(listecandidat)==0:
        return(None)
    else:
        affectationbis={}
        for voiture in listevoiture:
            liste=affectation[voiture][:]
            affectationbis[voiture]=liste
        m=randint(0,len(listecandidat)-1)
        affectationbis[listecandidat[m][1]]=listecandidat[m][0]
        if indicevoiture>=0:
            liste=affectation[voitureclient][:]
            liste.pop(indicedepose)
            liste.pop(indiceprise)
            affectationbis[voitureclient]=liste

    return(affectationbis)

def fluctuation2(affectation):
    affectationbis={}
    for voiture in affectation.keys():
        affectationbis[voiture]=affectation[voiture][:]
    listevoiture=["rejet"]
    for voiture in affectation.keys():
        if len(affectation[voiture])>2:
            listevoiture.append(voiture)
    m=randint(0,len(listevoiture)-1)
    n=randint(0,len(listevoiture)-2)
    voiture1=listevoiture.pop(m)
    voiture2=listevoiture.pop(n)
    if voiture1=="rejet":
        voiture1,voiture2=voiture2,voiture1
    m=randint(1,len(affectation[voiture1])-2)
    client1=clients[affectation[voiture1][m]]
    indice1=[]
    for k in range(1,len(affectation[voiture1])-1):
        if clients[affectation[voiture1][k]]==client1:
            indice1.append(k)
    #print(len(indice1))
    nouvelliste1=affectation[voiture1][:indice1[0]]+affectation[voiture1][indice1[0]+1:indice1[1]]+affectation[voiture1][indice1[1]+1:]


    if voiture2=="rejet":
        listerejet=[]
        listeservi=listeclientservi(affectation)
        for client in listeclient:
            if client not in listeservi:
                listerejet.append(client)
        m=randint(0,len(listerejet)-1)
        client2=listerejet[m]
    else:
        m=randint(1,len(affectation[voiture2])-2)
        client2=clients[affectation[voiture2][m]]
        indice2=[]
        for k in range(1,len(affectation[voiture2])-1):
            if clients[affectation[voiture2][k]]==client2:
                indice2.append(k)
        nouvelliste2=affectation[voiture2][:indice2[0]]+affectation[voiture2][indice2[0]+1:indice2[1]]+affectation[voiture2][indice2[1]+1:]
        listecandidat2=insertclient(client1,voiture2,nouvelliste2)
        if len(listecandidat2)>0:
            m=randint(0,len(listecandidat2)-1)
            nouvelliste2=listecandidat2[m]
        affectationbis[voiture2]=nouvelliste2
    listecandidat1=insertclient(client2,voiture1,nouvelliste1)
    if len(listecandidat1)>0:
        m=randint(0,len(listecandidat1)-1)
        nouvelliste1=listecandidat1[m]
    affectationbis[voiture1]=nouvelliste1
    return(affectationbis)







def fluctuation3(affectation):
    listerejet=[]
    listeservi=listeclientservi(affectation)
    for client in listeclient:
        if client not in listeservi:
            listerejet.append(client)
    listevoiture=[voiture for voiture in affectation.keys()]
    for client in listerejet:
        listecandidat=[]
        for voiture in listevoiture:
            candidatvoiturek=insertclient(client,voiture,affectation[voiture])
            for candidat in candidatvoiturek:
                listecandidat.append([candidat,voiture])
        if len(listecandidat)!=0:
            affectationbis={}
            for voiture in listevoiture:
                liste=affectation[voiture][:]

                affectationbis[voiture]=liste

            m=randint(0,len(listecandidat)-1)
            affectationbis[listecandidat[m][1]]=listecandidat[m][0]

            return(affectationbis)
    return(None)




epsilon=0
listejob=[x for x in depose.values()]+[x for x in prise.values()]
for job1 in listejob:
    for job2 in listejob:
        epsilon+=time[(station[job1],station[job2])]
epsilon=1/epsilon

def energie(affectation):
    return(len(listeclientservi(affectation))-epsilon*cout_total(affectation))




def recuit_simule(resjson,T0,Tmin,Lambda,nom):
    #applique l'algorithme du recuit simulé :
    #resjson est un dictionnaire correspondant au format json demandé

    def temperature(T):
        return(T*Lambda)
    T=T0
    res0=json2monformat(resjson)
    Emax=energie(res0)
    E0=Emax
    bestres=res0



    while T>Tmin:
        fluctuation=fluctuation1(res0)

        if fluctuation!=None:
            dif=energie(fluctuation)-energie(res0)
            if dif>=0:
                res0=fluctuation

                #print("gain d'energie")
                if energie(res0)>Emax:
                    Emax=energie(res0)
                    bestres=res0
            else:
                p=random()
                if p<exp(dif/T):
                    res0=fluctuation
                    #print("perte d'energie")
            T=temperature(T)


    plt.show()
    if Emax>E0:
        print("meilleur solution !")


    else:
        print("pas d'amelioration")

    with open(nom+".json", 'w', encoding='utf-8') as f:
        json.dump(monformat2json(bestres), f, indent=4)
    return(int(Emax)+1,cout_total(bestres))


#nom du fichier a changer pour essayer une  solution
with open("results/insertion_v1_eval.json") as json_data:
    resjson = json.load(json_data)

res0=json2monformat(resjson)

Lambda=0.9999
n=0
s=0
while n<50:
    fluctuation=fluctuation1(res0)
    if fluctuation!=None:
        s+=abs(energie(fluctuation)-energie(res0))
        n+=1
s/=n
T0=-s/log(0.99)
Tmin=-s/log(0.01)

# Debut du decompte du temps
start_time = clock.time()

recuit_simule(resjson,T0,Tmin,Lambda,"results/sa_eval_insertion_v1")

# Affichage du temps d execution
end_time = clock.time()
print("Temps d execution : %s secondes" % (end_time - start_time))



