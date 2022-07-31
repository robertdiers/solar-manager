#!/usr/bin/env python

import configparser
import os
from datetime import datetime
from urllib.request import urlopen

import TimescaleDb
import IdmPump
import Kostal
import Tasmota

#read config
config = configparser.ConfigParser()

# charger
def charger(charger_mqtt_name, surplus, charge_start, charge_end):
    try:
        retval = 'ON'

        #we will always charge between 12:00 and 12:05 to ensure a kind of "battery protect"
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            Tasmota.on(charger_mqtt_name)
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging battery protect: ", surplus)
            TimescaleDb.write('solar_battery_chargestatus', 1)
            retval = 'ON'
        else:
            if surplus > int(charge_start):
                Tasmota.on(charger_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging: ", surplus)
                TimescaleDb.write('solar_battery_chargestatus', 1)
                retval = 'ON'
            elif surplus < int(charge_end):
                Tasmota.off(charger_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger stop charging: ", surplus)
                TimescaleDb.write('solar_battery_chargestatus', 0)   
                retval = 'OFF'
            else:
                TimescaleDb.write('solar_battery_chargestatus', 0.5) 
                retval = 'UNCHANGED'
        
        return retval
    except Exception as ex:
        print ("ERROR Charger: ", ex)  

# idm heat pump
def idm(powerToGrid, feed_in_limit):
    try:
        #feed in must be above our limit
        feed_in = powerToGrid;
        if feed_in > feed_in_limit:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM feed-in reached: ", feed_in)               
            feed_in = feed_in/1000
        else:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM send ZERO: ", feed_in)  
            feed_in = 0
        
        #connection iDM
        IdmPump.connect()      
       
        IdmPump.writefloat(74,feed_in,1)
        TimescaleDb.write('solar_idm_feedin', (feed_in*1000))
            
        #read from iDM
        idmvalue = IdmPump.readfloat(74,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM: ", idmvalue)
        
        return idmvalue
    except Exception as ex:
        print ("ERROR Idm: ", ex) 
    finally:
        IdmPump.close()  

# metrics from Tasmota
def metrics():
    try:
        technical_room_temperature = Tasmota.get("tasmota_server", "8", "StatusSNS_SI7021_Temperature")
        TimescaleDb.write('technical_room_temperature', technical_room_temperature)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " technical_room_temperature: " + str(technical_room_temperature))  
    except Exception as ex:
        print ("ERROR: ", ex) 
    try:
        solar_battery_charger_power = Tasmota.get("tasmota_charger", "8", "StatusSNS_ENERGY_Power")
        TimescaleDb.write('solar_battery_charger_power', solar_battery_charger_power)
        solar_battery_charger_yesterday = Tasmota.get("tasmota_charger", "8", "StatusSNS_ENERGY_Yesterday")
        TimescaleDb.write('solar_battery_charger_yesterday', solar_battery_charger_yesterday)
        solar_battery_charger_today = Tasmota.get("tasmota_charger", "8", "StatusSNS_ENERGY_Today")
        TimescaleDb.write('solar_battery_charger_today', solar_battery_charger_today)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " solar_battery_charger_power: " + str(solar_battery_charger_power)+", solar_battery_charger_yesterday: " + str(solar_battery_charger_yesterday)+", solar_battery_charger_today: " + str(solar_battery_charger_today))  
    except Exception as ex:
        print ("ERROR: ", ex) 

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        feed_in_limit = int(config['IdmSection']['feed_in_limit']) 
        charge_start = config['ChargerSection']['charge_start']  
        charge_end = config['ChargerSection']['charge_end']  
        maxOutput = config['RS485Section']['maxOutput']
        charge_mqtt_name = config['ChargerSection']['charge_mqtt_name']

        # override with environment variables
        if os.getenv('FEED_IN_LIMIT','None') != 'None':
            feed_in_limit = os.getenv('FEED_IN_LIMIT')
            print ("using env: FEED_IN_LIMIT")
        if os.getenv('CHARGE_START','None') != 'None':
            charge_start = os.getenv('CHARGE_START')
            print ("using env: CHARGE_START")
        if os.getenv('CHARGE_END','None') != 'None':
            charge_end = os.getenv('CHARGE_END')
            print ("using env: CHARGE_END")
        if os.getenv('MAXOUTPUT','None') != 'None':
            maxOutput = os.getenv('MAXOUTPUT')
            print ("using env: MAXOUTPUT")
        if os.getenv('CHARGE_MQTT_NAME','None') != 'None':
            charge_mqtt_name = os.getenv('CHARGE_MQTT_NAME')
            print ("using env: CHARGE_MQTT_NAME")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " feed_in_limit: ", feed_in_limit)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_start: ", charge_start)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_end: ", charge_end)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " maxOutput: ", maxOutput)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_mqtt_name: ", charge_mqtt_name) 
        
        TimescaleDb.connect()
        Kostal.connect()
        Tasmota.connect()

        #all additional invertes will decrease my home consumption, so it might be negative - this is fine
        consumptionbat = Kostal.readfloat(106,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption battery: ", consumptionbat)
        #WriteTimescaleDb('solar_kostal_consumption_battery', consumptionbat)
        consumptiongrid = Kostal.readfloat(108,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption grid: ", consumptiongrid)
        #WriteTimescaleDb('solar_kostal_consumption_grid', consumptiongrid)
        consumptionpv = Kostal.readfloat(116,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption pv: ", consumptionpv)
        #WriteTimescaleDb('solar_kostal_consumption_pv', consumptionpv)

        #CONSUMPTION WILL NOT GET NEGATIVE!
        consumption_total = consumptionbat + consumptiongrid + consumptionpv
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: ", consumption_total)
        TimescaleDb.write('solar_kostal_consumption_total', consumption_total)

        inverter = Kostal.readfloat(172,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter: ", inverter)   
        TimescaleDb.write('solar_kostal_inverter', inverter)
        
        batteryamp = Kostal.readfloat(200,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (A): ", batteryamp)
        batteryvolt = Kostal.readfloat(216,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (V): ", batteryvolt)
        powerToBattery = -round(batteryamp * batteryvolt, 2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (W): ", battery)
        #TimescaleDb.write('solar_kostal_battery', battery)
        if batteryamp > 0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: discharge")
            TimescaleDb.write('solar_kostal_batteryflag', 0)
        elif batteryamp < -0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: charge")
            TimescaleDb.write('solar_kostal_batteryflag', 1)
        else:
            TimescaleDb.write('solar_kostal_batteryflag', 0.5)
        batterypercent = Kostal.readfloat(210,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)
        TimescaleDb.write('solar_kostal_batterypercent', (batterypercent/100))
        
        #Kostal generation (by tracker/battery)
        dc1 = Kostal.readfloat(260,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc1: ", dc1)
        #TimescaleDb.write('solar_kostal_generation_dc1', dc1)
        dc2 = Kostal.readfloat(270,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc2: ", dc2)
        #TimescaleDb.write('solar_kostal_generation_dc2', dc2)
        dc3 = Kostal.readfloat(280,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc3: ", dc3)
        #TimescaleDb.write('solar_kostal_generation_dc3', dc3)
        generation = round(dc1+dc2+dc3,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " generation: ", generation) 
        TimescaleDb.write('solar_kostal_generation_total', generation)       

        #this is not exact, but enough for us
        #powerToGrid = round(inverter - consumption_total,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        powerToGrid = -Kostal.readfloat(252,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        TimescaleDb.write('solar_kostal_powertogrid', powerToGrid)

        #this is not exact, but enough for us, wrong for negative consumption
        #surplus = round(generation - consumption_total,1)
        # if we send power to battery or grid
        surplus = round(powerToBattery + powerToGrid, 2)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: ", surplus)
        TimescaleDb.write('solar_kostal_surplus', surplus)

        dailyyield = round(Kostal.readfloat(322,71) / 1000,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dailyyield: ", dailyyield)
        TimescaleDb.write('solar_kostal_dailyyield', dailyyield)

        homeconsumption = round(Kostal.readfloat(118,71) / 1000 / 1000,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " homeconsumption: ", homeconsumption)
        TimescaleDb.write('solar_kostal_homeconsumption', homeconsumption)
        
        Kostal.close()
        
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: " + str(round(consumption_total,2)) + ", generation: " + str(generation) + ", surplus: " + str(surplus) + ", powerToBattery: " + str(powerToBattery) + ", powerToGrid: " + str(powerToGrid))   
        
        # charger - we need to substract actual soyosource value
        valuesoyosource = TimescaleDb.read('soyosource')
        chargersurplus = surplus - valuesoyosource

        chargerval = charger(charge_mqtt_name, chargersurplus, charge_start, charge_end)
        
        # idm
        idmval = idm(powerToGrid, feed_in_limit)

        # soyosource should not use battery during this time
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            surplus = 10000

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: " + str(surplus))  
        soyoval = TimescaleDb.increase('soyosource', -surplus, float(maxOutput))
        TimescaleDb.write('solar_soyosource', soyoval)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " soyoval: " + str(soyoval)) 

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charger: " + chargerval + ", iDM: " + str(idmval) + ", soyosource: " + str(round(soyoval,2)))  
    
        # metrics
        metrics()

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()     
