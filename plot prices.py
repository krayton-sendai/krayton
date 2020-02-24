# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 17:31:22 2020

@author: timot
"""

import matplotlib.pyplot as plt
import csv
'''
fig,ax=plt.subplots()
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
ax.plot([0,24],[14.658,14.658],label='octopus buy')
price=np.array([])       #Sell price always same as buy price
with open('sspsbpniv.csv',newline='') as csvfile:
    raw_price=csv.reader(csvfile,delimiter=',')
    for line in raw_price:
        price=np.append(price,float(line[2])/1000)    
m_list=np.zeros(48)
for t in range(len(price)):
    m_list[t%48]+=price[t]
m_list=m_list/(len(price)/48)
ax.plot(np.array(range(48))/2,m_list*100,label='wholesale')

ax.set_ylabel('price (p/kWh)')
ax.set_xlabel('time of day')
ax.set_xlim([0,24])
ax.legend()
''' 
fig,ax=plt.subplots()
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

def load_heat_data(village_annual_heat_demand):
    #Read degree day data from csv file
    #Use shape of degree day curve, scale to estimated heating demand
    import csv
    degree_day=[]
    #Science park floor area 264000 Houses floor area 236000*2 hot water 3e6 passive house 15kWh/yr
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

total_demand=(load_sciencepark()+load_heat_data(264000*15))
m_list=np.zeros(48)
for t in range(len(total_demand)):
    m_list[t%48]+=total_demand[t]
m_list=m_list/(len(total_demand)/48)
ax.plot(np.array(range(48))/2,m_list/1000,label='science park')
total_demand=(residential()+load_heat_data(236000*2*15))
m_list=np.zeros(48)
for t in range(len(total_demand)):
    m_list[t%48]+=total_demand[t]
m_list=m_list/(len(total_demand)/48)
ax.plot(np.array(range(48))/2,m_list/1000,label='homes')
ax.set_ylabel('power (MW)')
ax.set_xlabel('time of day')
ax.set_xlim([0,24])
fig.legend()