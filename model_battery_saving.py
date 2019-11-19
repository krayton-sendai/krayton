# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 12:43:05 2019

@author: Timothy Tam
"""

import numpy as np
import matplotlib.pyplot as plt


def solar_data():
    #Read solar data from csv file
    capacity_factor=[]
    import csv
    with open('solar_ouput_2014 _europe_fliped.csv',newline='') as csvfile:
        raw_solar_data=csv.reader(csvfile,delimiter=',')
        line = 0
        for row in raw_solar_data:
            #Column 2 of the solar data is hourly capacity factor, starting from line 4
            if line>=4:
                capacity_factor.append(float(row[2]))
            line+=1
    #Make hourly solar data to half hourly by taking average between two data point
    capacity_factor_half_hour=[]
    for hour in range(len(capacity_factor)):
        if hour<len(capacity_factor)-1:
            approx=(capacity_factor[hour]+capacity_factor[hour+1])*0.5  #Average of hourly data in front and behind
            capacity_factor_half_hour+=[capacity_factor[hour]*0.5,approx*0.5]   #x0.5 as dt is half hour
    capacity_factor_half_hour.append(capacity_factor[-1])
    return np.array(capacity_factor_half_hour)

def load_data():
    #Read load data from csv file
    #scales demand by population
    demand=[]
#    uk_annual_demand=143e6*0.01163  #UK demand in toe, convert into GWh
    village_annual_demand=120e6   #From our estimate, 120GWh per year
#    village_daily_demand=village_annual_demand/365  #Assume same everyday for now
    import csv
    with open('uk_annual_demand_fliped.csv',newline='') as csvfile:
#    with open('uk_demand_1108.csv',newline='') as csvfile:
        raw_demand_data=csv.reader(csvfile,delimiter=',')
        line=0
        for row in raw_demand_data:
            #Column 5 of demand data is half hourly capacity factor, starting from line 1
            if line>=1:
                demand.append(float(row[4]))
            line+=1
    #make weekly data into half hourly by linear approximating middle values
    hourly_demand=[]
    linear_list=np.array(range(336))
    for week in range(len(demand)):
        if week<len(demand)-1:
            week_demand=demand[week]+(demand[week+1]-demand[week])*linear_list/336
            hourly_demand=np.append(hourly_demand,week_demand)
        else:
            hourly_demand=np.append(hourly_demand,[demand[week]]*383)
    #scale the total consumption to out predictied consumption
    sum_hourly_demand=sum(hourly_demand)
    scaled_demand=hourly_demand/sum_hourly_demand*village_annual_demand
    return(scaled_demand)
        
def create_pv(pv,capacity,initial_cost,capacity_factor):
    #add new pv assest to pv dictionary
    pvid=len(pv)
    pv[pvid]={}
    pv[pvid]['capacity']=capacity               #in kWh
    pv[pvid]['initial_cost']=initial_cost       #in pounds
    pv[pvid]['output']=np.array(capacity_factor,dtype=float)*capacity #output = capacity x capacity factor, which gives power in kW
    return pv

def create_load(load,power_use):
    #add new load assest to load dictionary
    loadid=len(load)
    load[loadid]=np.array(power_use,dtype=float)
    return load

def create_storage(storage,capacity,power,efficiency,initial_cost):
    #add new storage to storage dictionary
    storageid=len(storage)
    storage[storageid]={}
    storage[storageid]['capacity']=capacity     #capacity of storage in kWh
    storage[storageid]['power']=power               #maximum input or output power of storage, after calculating efficiency
    storage[storageid]['efficiency']=efficiency     #efficiency of storage in both input or output
    storage[storageid]['initial_cost']=initial_cost #in pounds
    storage[storageid]['stored']=[0]                #start with empty storage
    return storage

def energy_system(pv,load,storage):
    total_output=np.array([0]*len(pv[0]['output']),dtype=float)
    for pvid in pv:
        total_output+=pv[pvid]['output']
    total_load=np.array([0]*len(load[0]),dtype=float)
    for loadid in load:
        total_load+=np.array(load[loadid])
    excess=total_output-total_load                  #Calculate excess power before using storage
    storage_time=0                                  #At time 0, storage has now charge. Storage records the charge avaliable for this time slot
    buy=[]                                          #Power bought from market, negative means sold
    balancing=[]                                    #Record power taken or given by storage to meet excess power, after accounting efficiency
    for dexcess in excess:                          #dexcess is the excess at this time slot
        balancing.append(0)
        for storageid in storage:                   #run through all storage facilities
        #charge power is the amount charged to storage
            if dexcess>=0:                          #pv > load, storage charging
                charge_power=min(dexcess*storage[storageid]['efficiency'],storage[storageid]['capacity']-storage[storageid]['stored'][storage_time],storage[storageid]['power'])    #charge power is the lesser of dexcess or remaining space of storage 
                dexcess-=charge_power/storage[storageid]['efficiency']      #amount of power taken from dexcess, after accounting efficiency
                balancing[storage_time]-=charge_power/storage[storageid]['efficiency']
            else:                                   #pv < load, storage discharging
                charge_power=max(dexcess/storage[storageid]['efficiency'],-storage[storageid]['stored'][storage_time],-storage[storageid]['power'])  #charge power is the less negative of dexcess or remaining charge
                dexcess-=charge_power*storage[storageid]['efficiency']      #amount of power given to dexcess, after accounting efficiency
                balancing[storage_time]-=charge_power*storage[storageid]['efficiency']
            storage[storageid]['stored'].append(storage[storageid]['stored'][storage_time]+charge_power)
        storage_time+=1
        buy.append(-dexcess)
    return [buy,total_output,total_load,balancing]

def plot_demand(total_output,total_load,balancing):
    total_energy_production=sum(total_output)
    total_energy_consumption=sum(total_load)
    print('Total energy production is ',total_energy_production,'kWh Total energy consumption is ',total_energy_consumption,'kWh')
    time_list=np.array(range(len(balancing)))/48
    labels=['total output','storage operation']
    fig,ax=plt.subplots()
    p1=ax.stackplot(time_list,total_output,balancing,labels=labels)
    p2=ax.plot(time_list,total_load,'-',label='total load')
    plt.ylabel('power (kW)')
    plt.xlabel('time (day)')
    fig.legend()
    plt.show()
    

def market(buy,sell_price,buy_price):
    cost=0
    for energy in buy:
        if energy <0:
            price=energy*sell_price
        else:
            price=energy*buy_price
        cost+=price
    return cost

def captial_cost(pv,storage):
    cost=0
    for pvid in pv:
        cost+=pv[pvid]['initial_cost']
    for storageid in storage:
        cost+=storage[storageid]['initial_cost']
    return cost



#Uncomment below to get cost saved by installing storage

buy_price=0.143    #Price for buying electricity
sell_price=0.0524   #Price for selling electricity
storage_price=150  #Price of storage per kWh
pv_price=100       #Price of PV per kWp
duration=10        #Life of PV and storage

#Create load by create_load(load,list of load power in time)
uk_scaled_load=load_data()
load=create_load({},uk_scaled_load)

capacity_factor=solar_data()
pv_list=np.array(range(1,6))*20000
storage_list=np.array(range(1,13))*2e4
storage_list_price=storage_list*storage_price/duration
color_list=['r-','g-','b-','y-','m-']
color_id=0

fig,ax=plt.subplots()
refernence_list=[0,3600]
ax.plot(refernence_list,refernence_list,'k-',label='reference' )
for pv_capacity in pv_list:
    cost_saved_list=[]
    #Reference of system with 0 storage
    storage={}
    #Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
    storage=create_storage(storage,0,10000000,1,0)
    #Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
    pv=create_pv({},pv_capacity,pv_capacity*pv_price/duration,capacity_factor)        
    [buy,total_output,total_load,balancing]=energy_system(pv,load,storage)
    running_cost0=market(buy,sell_price,buy_price)
    for storage_capacity in storage_list:
        storage={}
        #Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
        storage=create_storage(storage,storage_capacity,10000000,1,storage_capacity*storage_price/duration)
        #Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
        pv=create_pv({},pv_capacity,pv_capacity*10,capacity_factor)        
        [buy,total_output,total_load,balancing]=energy_system(pv,load,storage)
        running_cost=market(buy,sell_price,buy_price)
        cost_saved=running_cost0-running_cost
        cost_saved_list.append(cost_saved)
    ax.plot([i/1000 for i in storage_list_price],[i/1000 for i in cost_saved_list],color_list[color_id],label='pv = '+str(pv_capacity/1000)+'MW')
    color_id+=1

plt.ylabel('cost saved (thousand)')
plt.xlabel('storage price (thousand)')
fig.legend(loc='upper center', bbox_to_anchor=(1.1, 0.8), shadow=True, ncol=1)
plt.show()



#Uncomment below to get total system price

#Create load by create_load(load,list of load power in time)
#uk_scaled_load=load_data()
#load=create_load(load,uk_scaled_load)

#capacity_factor=solar_data()
#pv_list=np.array(range(12))*10000
#storage_list=np.array(range(5))*8e6
#
#fig,ax=plt.subplots()
#for storage_capacity in storage_list:        
#    total_cost_list=[]
#    for pv_capacity in pv_list:
#        storage={}
#        #Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
#        storage=create_storage(storage,storage_capacity,10000000,1,storage_capacity*15)
#        #Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
#        pv=create_pv({},pv_capacity,pv_capacity*10,capacity_factor)        
#        [buy,total_output,total_load,balancing]=energy_system(pv,load,storage)
#        running_cost=market(buy,sell_price,buy_price)
#        initial_cost= captial_cost(pv,storage)
#        total_cost=running_cost+initial_cost
#        total_cost_list.append(total_cost)
#    ax.plot(pv_list,total_cost_list,'-',label='storage = '+str(storage_capacity/1000000)+'GWh')
#plt.ylabel('cost')
#plt.xlabel('PV capacity (kWp)')
#fig.legend(loc='upper center', bbox_to_anchor=(1.02, 1), shadow=True, ncol=1)
#plt.show()



