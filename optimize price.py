# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 12:43:05 2019

@author: Timothy Tam
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import csv
import statistics


#dictionaries for storing information of pv, load, storage
pv={}
load={}
storage={}

def electricity_price_retail():
    buy_price=np.tile([0.14658],52560)
    sell_price=np.array([])
    with open('sell_price.csv',newline='') as csvfile:
        raw_electricity_price=csv.reader(csvfile,delimiter=',')
        #Price of selling to grid
        for line in raw_electricity_price:
            sell_price=np.append(sell_price,float(line[0]))
    sell_price=sell_price/100
    m_list=np.zeros(48)
    for t in range(len(sell_price)):
        m_list[t%48]+=sell_price[t]
    m_list=m_list/(len(sell_price)/48)
    ax.plot(np.array(range(48))/2,m_list*100,label='octopus sell')
#    fig,ax=plt.subplots()
#    for t in range(int(len(sell_price)/48)-48):
#        ax.plot(np.array(range(48))/2,sell_price[48*t:48*(t+1)])
    return [buy_price,sell_price]

def electricity_price_wholesale():
    price=np.array([])       #Sell price always same as buy price
    with open('sspsbpniv.csv',newline='') as csvfile:
        raw_price=csv.reader(csvfile,delimiter=',')
        for line in raw_price:
            price=np.append(price,float(line[2])/1000)    
    m_list=np.zeros(48)
    for t in range(len(price)):
        m_list[t%48]+=price[t]
    m_list=m_list/(len(price)/48)
#    fig,ax=plt.subplots()
    ax.plot(np.array(range(48))/2,m_list*100,label='wholesale')
#    fig,ax=plt.subplots()
#    for t in range(int(len(price)/48)-48):
#        ax.plot(np.array(range(48))/2,price[48*t:48*(t+1)])
    price=np.tile(price,3)
    return [price,price]

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
    capacity_factor_half_hour=[0]
    for hour in range(len(capacity_factor)):
        if hour<len(capacity_factor)-1:
            approx=(capacity_factor[hour]+capacity_factor[hour+1])*0.5  #Average of hourly data in front and behind
            capacity_factor_half_hour+=[capacity_factor[hour]*0.5,approx*0.5]   #x0.5 as dt is half hour
    capacity_factor_half_hour.append(capacity_factor[-1])
    capacity_factor_half_hour=np.tile(capacity_factor_half_hour,3)
    return np.array(capacity_factor_half_hour)

def solar_data_flat():
    import csv
    with open('solar_ouput_2014_europe_flat.csv',newline='') as csvfile:
        raw_flat=csv.reader(csvfile,delimiter=',')
        for line in raw_flat:
           capacity_factor_flat=[float(h) for h in line]
    capacity_factor_half_hour_flat=[0]
    for hour in range(len(capacity_factor_flat)):
        if hour<len(capacity_factor_flat)-1:
            approx=(capacity_factor_flat[hour]+capacity_factor_flat[hour+1])*0.5  #Average of hourly data in front and behind
            capacity_factor_half_hour_flat+=[capacity_factor_flat[hour]*0.5,approx*0.5]   #x0.5 as dt is half hour
    capacity_factor_half_hour_flat.append(capacity_factor_flat[-1])
    capacity_factor_half_hour_flat=np.tile(capacity_factor_half_hour_flat,3)
    return np.array(capacity_factor_half_hour_flat)

def solar_data_10():
    import csv
    with open('solar_ouput_2014_europe_10.csv',newline='') as csvfile:
        raw_10=csv.reader(csvfile,delimiter=',')
        for line in raw_10:
           capacity_factor_10=[float(h) for h in line]
    capacity_factor_half_hour_10=[0]
    for hour in range(len(capacity_factor_10)):
        if hour<len(capacity_factor_10)-1:
            approx=(capacity_factor_10[hour]+capacity_factor_10[hour+1])*0.5  #Average of hourly data in front and behind
            capacity_factor_half_hour_10+=[capacity_factor_10[hour]*0.5,approx*0.5]   #x0.5 as dt is half hour
    capacity_factor_half_hour_10.append(capacity_factor_10[-1])
    capacity_factor_half_hour_10=np.tile(capacity_factor_half_hour_10,3)
    return np.array(capacity_factor_half_hour_10)


def residential():
    village_annual_demand=11.88e6
    profile_demand=np.zeros(365*48)
    t=0
    import csv
    with open('residential.csv',newline='') as csvfile:
        raw_residential=csv.reader(csvfile,delimiter=',')
        for row in raw_residential:
            for item in row:
                profile_demand[t]=float(item)
                t+=1
    sum_profile_demand=sum(profile_demand)
    scaled_profile_demand=profile_demand/sum_profile_demand*village_annual_demand
#    plt.plot(list(range(len(scaled_profile_demand))),scaled_profile_demand,'-')
    scaled_profile_demand=np.tile(scaled_profile_demand,3)
    return(scaled_profile_demand)
            

def load_heat_data():
    #Read degree day data from csv file
    #Use shape of degree day curve, scale to estimated heating demand
    import csv
    degree_day=[]
    #Science park floor area 264000 Houses floor area 236000*2 hot water 3e6 passive house 15kWh/yr
    village_annual_heat_demand=236000*2*15
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
    half_hourly_demand=np.append(half_hourly_demand,half_hourly_demand[len(half_hourly_demand)-1])
    sum_half_hourly_demand=sum(half_hourly_demand)
    scaled_heat_demand=half_hourly_demand/sum_half_hourly_demand*village_annual_heat_demand
    scaled_heat_demand=np.tile(scaled_heat_demand,3)
    return(scaled_heat_demand)
    
def load_sciencepark():
    #Read average electricity consumption of CIE science park
    #Average of 2017 and 2018, unit: kWh/30min
    import csv
    CIE_demand=np.zeros(365*48)
    count=0
    science_park_demand=354748*44   #Estimated using ratio of building area
    with open('science_park_electricity.csv',newline='') as csvfile:
        raw_sciencepark=csv.reader(csvfile,delimiter=',')
        for row in raw_sciencepark: #Each row is a day
            for t in row:           #Each t repersent a half hour period demand
                CIE_demand[count]=float(t)
                count+=1
    sum_CIE_demand=sum(CIE_demand)
    scaled_science_park_demand=CIE_demand/sum_CIE_demand*science_park_demand
    scaled_science_park_demand=np.tile(scaled_science_park_demand,3)
    return(scaled_science_park_demand)
        
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

def energy_system_wholesale_opt(pv,load,storage,buy_price,sell_price):
    total_output=np.array([0]*len(pv[0]['output']),dtype=float)
    for pvid in pv:
        total_output+=pv[pvid]['output']
    total_load=np.array([0]*len(load[0]),dtype=float)
    for loadid in load:
        total_load+=np.array(load[loadid])
    excess=total_output-total_load                  #Calculate excess power before using storage
    storage_time=0                                  #At time 0, storage has no charge. Storage records the charge avaliable for this time slot
    buy=[]                                          #Power bought from market, negative means sold
    balancing=[]                                    #Record power taken or given by storage to meet excess power, after accounting efficiency
    sum_sell_price=0                                #Record of previous sum to calculate mean
    sell_i=0                                        #Record number of time slot when there is excess
    sum_buy_price=0
    buy_i=0
    for dexcess in excess:                          #dexcess is the excess at this time slot
        balancing.append(0)
        for storageid in storage:                   #run through all storage facilities
        #charge power is the amount charged to storage
            if dexcess>=0:                          #pv > load
                sum_sell_price+=buy_price[storage_time]
                sell_i+=1
                m_sell=sum_sell_price/sell_i                   #Mean only calculated by dividing the number of time we have excess generation
                if sell_price[storage_time]<=m_sell:                    #selling price < median and selling price<buy price, storage charging
                    charge_power=min(dexcess*storage[storageid]['efficiency'],storage[storageid]['capacity']-storage[storageid]['stored'][storage_time],storage[storageid]['power'])    #charge power is the lesser of dexcess or remaining space of storage 
                    dexcess-=charge_power/storage[storageid]['efficiency']      #amount of power taken from dexcess, after accounting efficiency
                    balancing[storage_time]-=charge_power/storage[storageid]['efficiency']
                elif sell_price[storage_time]>0.058:                               #Sell all we can sell in storage when sell price > buy price
                    charge_power=-min(storage[storageid]['stored'][storage_time],storage[storageid]['power'])
                    dexcess-=charge_power*storage[storageid]['efficiency']
                    balancing[storage_time]-=charge_power*storage[storageid]['efficiency']
                else:
                    charge_power=0
            else:                                   #pv < load
                sum_buy_price+=buy_price[storage_time]
                buy_i+=1
                m_buy=sum_buy_price/buy_i
                if sell_price[storage_time]>=m_buy:            #Use storage only when buying price>m
                    charge_power=max(dexcess/storage[storageid]['efficiency'],-storage[storageid]['stored'][storage_time]*storage[storageid]['efficiency'],-storage[storageid]['power'])  #charge power is the less negative of dexcess or remaining charge
                    dexcess-=charge_power*storage[storageid]['efficiency']      #amount of power given to dexcess, after accounting efficiency
                    balancing[storage_time]-=charge_power*storage[storageid]['efficiency']
                elif buy_price[storage_time]<0.043:
                    charge_power=min(storage[storageid]['capacity']-storage[storageid]['stored'][storage_time],storage[storageid]['power'])
                    dexcess-=charge_power*storage[storageid]['efficiency']
                    balancing[storage_time]-=charge_power*storage[storageid]['efficiency']
                else:                               #Else, buy from grid
                    charge_power=0
            storage[storageid]['stored'].append(storage[storageid]['stored'][storage_time]+charge_power)
        storage_time+=1
        buy.append(-dexcess)
    return [buy,total_output,total_load,balancing]

def energy_system_retail_opt(pv,load,storage,buy_price,sell_price):
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
                if sell_price[storage_time]<=buy_price[storage_time]:       #Only charge when sell price<buy price
                    charge_power=min(dexcess*storage[storageid]['efficiency'],storage[storageid]['capacity']-storage[storageid]['stored'][storage_time],storage[storageid]['power'])    #charge power is the lesser of dexcess or remaining space of storage 
                    dexcess-=charge_power/storage[storageid]['efficiency']      #amount of power taken from dexcess, after accounting efficiency
                    balancing[storage_time]-=charge_power/storage[storageid]['efficiency']
                elif sell_price[storage_time]<=sell_price[storage_time-1]:       #Sell everything when buy price>sell price
                    charge_power=-min(storage[storageid]['power'],storage[storageid]['stored'][storage_time])
                    dexcess-=charge_power/storage[storageid]['efficiency']      #amount of power taken from dexcess, after accounting efficiency
                    balancing[storage_time]-=charge_power/storage[storageid]['efficiency']                    
            else:                                   #pv < load, storage discharging
                if buy_price[storage_time]>sell_price[storage_time]:        #Only use storage when buy price<sell price
                    charge_power=max(dexcess/storage[storageid]['efficiency'],-storage[storageid]['stored'][storage_time],-storage[storageid]['power'])  #charge power is the less negative of dexcess or remaining charge
                    dexcess-=charge_power*storage[storageid]['efficiency']      #amount of power given to dexcess, after accounting efficiency
                    balancing[storage_time]-=charge_power*storage[storageid]['efficiency']
                else:
                    charge_power=0
            storage[storageid]['stored'].append(storage[storageid]['stored'][storage_time]+charge_power)
        storage_time+=1
        buy.append(-dexcess)
    return [buy,total_output,total_load,balancing]


'''
def plot_demand(total_output,total_load,balancing):
    year_output=total_output[-21504:-3985]
    year_load=total_load[-21504:-3985]
    total_energy_production=sum(year_output)
    total_energy_consumption=sum(year_load)
    print(total_energy_consumption/total_energy_production)
    print('Total energy production is ',total_energy_production,'kWh Total energy consumption is ',total_energy_consumption,'kWh')
    time_list=pd.date_range(start='2015-01-01',end='2015-12-31',periods=len(year_load))
    year_balancing=np.array(balancing[-21504:-3985])
    labels=['total output','storage operation']
    fig,ax=plt.subplots()
    fmt=mdates.DateFormatter('%b')
    ax.xaxis.set_major_formatter(fmt)
    p1=ax.stackplot(time_list,year_output/1000,year_balancing/1000,labels=labels)
    p2=ax.plot(time_list,year_load/1000,'-k',label='total load')
    ax.set_xlim([time_list[0],time_list[-1]])
    plt.ylabel('power (kW)')
    plt.xlabel('time')
    fig.legend()
    plt.show()
'''    

def market(buy,sell_price,buy_price):
    cost=0
    for t in range(len(buy)):
        if buy[t] <0:
            price=buy[t]*sell_price[t]
        else:
            price=buy[t]*buy_price[t]
        cost+=price
    return cost

def captial_cost(pv,storage):
    cost=0
    for pvid in pv:
        cost+=pv[pvid]['initial_cost']
    for storageid in storage:
        cost+=storage[storageid]['initial_cost']
    return cost
'''
#Minimize runnging cost for houses
#Create load by create_load(load,list of load power in time)
heat_demand=load_heat_data()
load=create_load(load,residential())
load=create_load(load,heat_demand)
#Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
pv=create_pv(pv,46000,46000*56.95,solar_data())
#pv=create_pv(pv,17600,10*17600,solar_data_flat())
#pv=create_pv(pv,2400,10*2400,solar_data_10())

#Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
#Optimum storage for houses with maximum amount of PV in an unoptimize system = 17000kWh
storage=create_storage({},17000,17000,1,17000*15)
[buy,total_output,total_load,balancing]=energy_system_retail_opt(pv,load,storage,buy_price,sell_price)
running_cost=market(buy[-21504:-3985],sell_price[-21504:-3985],buy_price)
initial_cost=captial_cost(pv,storage)
total_cost=running_cost+initial_cost
print(running_cost)
'''

#Generation of Science Park roughly equal to demand so assume maximum amount of PV on science park
#Uncomment below to get battery size with minimum total cost

[buy_price,sell_price]=electricity_price_retail()
#Create load by create_load(load,list of load power in time)
heat_demand=load_heat_data()
load=create_load(load,residential())
load=create_load(load,heat_demand)
#load=create_load(load,load_sciencepark())
#Create pv assest by create_pv(pv,capacity,initial_cost,capacity_factor)
pv=create_pv(pv,46000,46000*10,solar_data())
#pv=create_pv(pv,17600,10*17600!,solar_data_flat())
#pv=create_pv(pv,2400,10*2400,solar_data_10())

#Create storage by create_storage(stroage,capacity,charge and discharge power, efficiency,initial cost)
#Optimum storage for science park in an unoptimize system = 10000kWh
storage=create_storage({},10000,10000,1,10000*15)
[buy,total_output,total_load,balancing]=energy_system(pv,load,storage,buy_price,sell_price)
running_cost=market(buy[-21504:-3985],sell_price[-21504:-3985],buy_price)
initial_cost=captial_cost(pv,storage)
total_cost=running_cost+initial_cost
print(running_cost)
