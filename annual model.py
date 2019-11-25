# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 12:43:05 2019

@author: Timothy Tam
"""

import numpy as np
import matplotlib.pyplot as plt

buy_price=0.15    #Price for buying electricity
sell_price=0.0    #Price for selling electricity

#dictionaries for storing information of pv, load, storage
pv={}
load={}
storage={}

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
    #Make hourly solar data to half hourly by taking average between teo data point
    capacity_factor_half_hour=[]
    for hour in range(len(capacity_factor)):
        if hour<len(capacity_factor)-1:
            approx=(capacity_factor[hour]+capacity_factor[hour+1])*0.5  #Average of hourly data in front and behind
            capacity_factor_half_hour+=[capacity_factor[hour]*0.5,approx*0.5]   #x0.5 as dt is half hour
    capacity_factor_half_hour.append(capacity_factor[-1])
    return np.array(capacity_factor_half_hour)

def load_data():
    #Read load data from csv file
    #scales UK demand by village demand
    demand=[]
#    uk_annual_demand=143e6*0.01163  #UK demand in toe, convert into GWh
    village_annual_demand=11.88e6   #From our estimate, 120GWh per year
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

def load_heat_data():
    #Read degree day data from csv file
    #Use shape of degree day curve, scale to estimated heating demand
    import csv
    degree_day=[]
    village_annual_heat_demand=46.94e6/3
    with open('2014degreedays.csv',newline='') as csvfile:
        raw_heat_demand_data=csv.reader(csvfile,delimiter=',')
        #Column 3 = HDD 10.5C, Column 4 = HDD 15.5C, Column 5 = HDD 18.5C, starting from line 1
        line=0
        column=5
        for row in raw_heat_demand_data:            
            if line>=1:
                degree_day.append(float(row[column]))
            line+=1
    #Make daily data to half hourly by linear approximating middle values
    half_hourly_demand=np.array([])
    linear_list=np.array(range(48))/48
    for day in range(len(degree_day)):
        if day<len(degree_day)-1:
            day_linear=degree_day[day]+(degree_day[day+1]-degree_day[day])*linear_list
            half_hourly_demand=np.append(half_hourly_demand,day_linear)
        else:
            half_hourly_demand=np.append(half_hourly_demand,[degree_day[day]]*47)
    sum_half_hourly_demand=sum(half_hourly_demand)
    scaled_heat_demand=half_hourly_demand/sum_half_hourly_demand*village_annual_heat_demand
#    plt.plot(list(range(len(scaled_heat_demand))),scaled_heat_demand,'-')
    return(scaled_heat_demand)
        
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
    storage[storageid]['capacity']=capacity         #capacity of storage in kWh
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
    p2=ax.plot(time_list,total_load,'-k',label='total load')
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

#capacity_factor=solar_data()
capacity_factor=solar_data()
#Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
pv_capacity=26200
loss=0.1
actual_pv_capacity=pv_capacity*(1-loss)
pv=create_pv(pv,actual_pv_capacity,pv_capacity*10,capacity_factor)
#Create load by create_load(load,list of load power in time)
uk_scaled_load=load_data()
heat_demand=load_heat_data()
load=create_load(load,uk_scaled_load)
load=create_load(load,heat_demand)
#Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
capacity=44000
storage=create_storage(storage,capacity,600000,1,capacity*15)
[buy,total_output,total_load,balancing]=energy_system(pv,load,storage)
running_cost=market(buy,sell_price,buy_price)
initial_cost=captial_cost(pv,storage)
total_cost=running_cost+initial_cost
plot_demand(total_output,total_load,balancing)
print('Operating cost is ',running_cost, ', initial cost is ',initial_cost,', total cost is ',total_cost)