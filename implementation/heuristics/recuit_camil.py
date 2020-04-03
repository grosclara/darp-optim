from insertion import *
from random import randint,random
from numpy import exp

epsilon=0
listejob=[x for x in drop_off.values()]+[x for x in pick_up.values()]
for job1 in listejob:
    for job2 in listejob:
        epsilon+=time[(station[job1],station[job2])]
epsilon=1/epsilon



def fluctuation1(affectation,listeclientrejete):
    listeclientrejetebis=listeclientrejete[:]
    m=randint(0,len(sorted_clients)-1)
    client=sorted_clients[m][1]
    listevoiture=[voiture for voiture in affectation.keys()]
    indicevoiture=-1
    if client not in unassigned_clients:
        arret=False
        for k in range(len(listevoiture)):
            for i in range(1,len(affectation[listevoiture[k]])-1):
                if clients[affectation[listevoiture[k]][i][0]]==client:
                    indiceprise=i
                    indicevoiture=k
                    indicedepose=None
                    for j in range(i+1,len(affectation[listevoiture[k]])-1):
                        if clients[affectation[listevoiture[k]][j][0]]==client:
                            indicedepose=j
                            break
                    if indicedepose==None:
                        print(affectation[listevoiture[k]])
                        print("erreur")#normalement cette partie ne sert à rien

                    arret=True
                    break
            if arret:
                break
        voitureclient=listevoiture.pop(indicevoiture)
    listecandidat=[]
    for voiture in listevoiture:
        candidatvoiturek=insert_client(client,voiture,affectation[voiture])
        for candidat in candidatvoiturek:
            listecandidat.append([candidat,voiture])
    if len(listecandidat)==0:
        return(None)
    else:
        affectationbis={}
        for voiture in listevoiture:
            liste=[]
            for course in affectation[voiture]:
                liste.append(course[:])
            affectationbis[voiture]=liste

        m=randint(0,len(listecandidat)-1)
        affectationbis[listecandidat[m][1]]=listecandidat[m][0]
        if indicevoiture>=0:
            liste=[]
            for course in affectation[voitureclient]:
                liste.append(course[:])
            liste.pop(indicedepose)
            liste.pop(indiceprise)
            affectationbis[voitureclient]=liste
        else:
            listeclientrejetebis.append(client)
    return(affectationbis,listeclientrejetebis)

def energie(affectation, listeclientrejete):
    return(len(sorted_clients)-len(listeclientrejete)-epsilon*global_cost(affectation))




def recuit_simule(res0,clientrejete0,T0,Tmin,Lambda):
    #applique l'algorithme du recuit simulé : renvoie True si a solution est trouvée est meilleur, False sinon

    def temperature(T,n):
        return(T*Lambda)
    n=0
    T=T0
    Emax=energie(res0,clientrejete0)
    E0=Emax
    bestres=res0
    bestclientrejete=clientrejete0

    while T>Tmin:
        fluctuation=fluctuation1(res0,clientrejete0)
        if fluctuation!=None:
            dif=energie(fluctuation[0],fluctuation[1])-energie(res0,clientrejete0)
            if dif>0:
                res0=fluctuation[0]
                clientrejete0=fluctuation[1]
                #print("gain d'energie")
                if energie(shift_schedules,unassigned_clients)>Emax:
                    Emax=energie(shift_schedules,unassigned_clients)
                    bestres=res0
                    bestclientrejete=clientrejete0
            else:
                p=random()
                if p<exp(dif/T):
                    res0=fluctuation[0]
                    clientrejete0=fluctuation[1]
                    #print("perte d'energie")
        T=temperature(T,n)
        n+=1

    if Emax>E0:
        print("meilleur sloution !")
        nom="essai_T0="+str(T0)+"_Tmin="+str(Tmin)+"_Lambda="+str(Lambda)
        nom=nom.replace('.',',')
        ecriturejson(bestclientrejete,bestres,nom)
        return(True)
    else:
        print("pas d'amelioration")
        return(False)


res0={}
for voiture in shift_schedules.keys():
    liste=[]
    for course in shift_schedules[voiture]:
        liste.append(course[:])
    res0[voiture]=liste
clientrejete0=unassigned_clients[:]

#parametre a changé

T0=1*(10**(-6))
Tmin=0.1*T0
Lambda=0.995
recuit_simule(res0,clientrejete0,T0,Tmin,Lambda)



