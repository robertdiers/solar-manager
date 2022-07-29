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
def Charger(conn, tasmota_mqtt_name, surplus, tasmota_charge_start, tasmota_charge_end):
    try:
        retval = 'ON'

        # Tasmota mqtt client
        mqtt_client = Tasmota.connect()

        #we will always charge between 12:00 and 12:05 to ensure a kind of "battery protect"
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            Tasmota.on(mqtt_client, tasmota_mqtt_name)
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging battery protect: ", surplus)
            TimescaleDb.write(conn, 'solar_battery_chargestatus', 1)
            retval = 'ON'
        else:
            if surplus > int(tasmota_charge_start):
                Tasmota.on(mqtt_client, tasmota_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging: ", surplus)
                TimescaleDb.write(conn, 'solar_battery_chargestatus', 1)
                retval = 'ON'
            elif surplus < int(tasmota_charge_end):
                Tasmota.off(mqtt_client, tasmota_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger stop charging: ", surplus)
                TimescaleDb.write(conn, 'solar_battery_chargestatus', 0)   
                retval = 'OFF'
            else:
                TimescaleDb.write(conn, 'solar_battery_chargestatus', 0.5) 
                retval = 'UNCHANGED'
        
        return retval
    except Exception as ex:
        print ("ERROR Charger: ", ex)  

# idm heat pump
def Idm(conn, powerToGrid, feed_in_limit):
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
        idmclient = IdmPump.connect()      
       
        IdmPump.writefloat(idmclient,74,feed_in,1)
        TimescaleDb.write(conn, 'solar_idm_feedin', (feed_in*1000))
            
        #read from iDM
        idmvalue = IdmPump.readfloat(idmclient,74,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM: ", idmvalue)
            
        IdmPump.close(idmclient)  
        return idmvalue
    except Exception as ex:
        print ("ERROR Idm: ", ex) 

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        feed_in_limit = int(config['IdmSection']['feed_in_limit']) 
        tasmota_charge_start = config['ChargerSection']['tasmota_charge_start']  
        tasmota_charge_end = config['ChargerSection']['tasmota_charge_end']  
        maxOutput = config['RS485Section']['maxOutput']
        tasmota_mqtt_name = config['ChargerSection']['tasmota_mqtt_name']

        # override with environment variables
        if os.getenv('FEED_IN_LIMIT','None') != 'None':
            feed_in_limit = os.getenv('FEED_IN_LIMIT')
            print ("using env: FEED_IN_LIMIT")
        if os.getenv('TASMOTA_CHARGE_START','None') != 'None':
            tasmota_charge_start = os.getenv('TASMOTA_CHARGE_START')
            print ("using env: TASMOTA_CHARGE_START")
        if os.getenv('TASMOTA_CHARGE_END','None') != 'None':
            tasmota_charge_end = os.getenv('TASMOTA_CHARGE_END')
            print ("using env: TASMOTA_CHARGE_END")
        if os.getenv('MAXOUTPUT','None') != 'None':
            maxOutput = os.getenv('MAXOUTPUT')
            print ("using env: MAXOUTPUT")
        if os.getenv('TASMOTA_MQTT_NAME','None') != 'None':
            tasmota_mqtt_name = os.getenv('TASMOTA_MQTT_NAME')
            print ("using env: TASMOTA_MQTT_NAME")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " feed_in_limit: ", feed_in_limit)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_charge_start: ", tasmota_charge_start)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_charge_end: ", tasmota_charge_end)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " maxOutput: ", maxOutput)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_mqtt_name: ", tasmota_mqtt_name)
        
        #init Timescaledb
        conn = TimescaleDb.connect()

        #connection Kostal
        inverterclient = Kostal.connect()       
        
        #all additional invertes will decrease my home consumption, so it might be negative - this is fine
        consumptionbat = Kostal.readfloat(inverterclient,106,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption battery: ", consumptionbat)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_battery', consumptionbat)
        consumptiongrid = Kostal.readfloat(inverterclient,108,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption grid: ", consumptiongrid)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_grid', consumptiongrid)
        consumptionpv = Kostal.readfloat(inverterclient,116,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption pv: ", consumptionpv)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_pv', consumptionpv)

        #CONSUMPTION WILL NOT GET NEGATIVE!
        consumption_total = consumptionbat + consumptiongrid + consumptionpv
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: ", consumption_total)
        TimescaleDb.write(conn, 'solar_kostal_consumption_total', consumption_total)

        inverter = Kostal.readfloat(inverterclient,172,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter: ", inverter)   
        TimescaleDb.write(conn, 'solar_kostal_inverter', inverter)
        
        batteryamp = Kostal.readfloat(inverterclient,200,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (A): ", batteryamp)
        batteryvolt = Kostal.readfloat(inverterclient,216,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (V): ", batteryvolt)
        powerToBattery = -round(batteryamp * batteryvolt, 2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (W): ", battery)
        #TimescaleDb.write(conn, 'solar_kostal_battery', battery)
        if batteryamp > 0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: discharge")
            TimescaleDb.write(conn, 'solar_kostal_batteryflag', -1)
        elif batteryamp < -0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: charge")
            TimescaleDb.write(conn, 'solar_kostal_batteryflag', 1)
        else:
            TimescaleDb.write(conn, 'solar_kostal_batteryflag', 0)
        batterypercent = Kostal.readfloat(inverterclient,210,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)
        TimescaleDb.write(conn, 'solar_kostal_batterypercent', (batterypercent/100))
        
        #Kostal generation (by tracker/battery)
        dc1 = Kostal.readfloat(inverterclient,260,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc1: ", dc1)
        #TimescaleDb.write(conn, 'solar_kostal_generation_dc1', dc1)
        dc2 = Kostal.readfloat(inverterclient,270,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc2: ", dc2)
        #TimescaleDb.write(conn, 'solar_kostal_generation_dc2', dc2)
        dc3 = Kostal.readfloat(inverterclient,280,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc3: ", dc3)
        #TimescaleDb.write(conn, 'solar_kostal_generation_dc3', dc3)
        generation = round(dc1+dc2+dc3,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " generation: ", generation) 
        TimescaleDb.write(conn, 'solar_kostal_generation_total', generation)       

        #this is not exact, but enough for us
        #powerToGrid = round(inverter - consumption_total,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        powerToGrid = -Kostal.readfloat(inverterclient,252,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        TimescaleDb.write(conn, 'solar_kostal_powertogrid', powerToGrid)

        #this is not exact, but enough for us, wrong for negative consumption
        #surplus = round(generation - consumption_total,1)
        # if we send power to battery or grid
        surplus = round(powerToBattery + powerToGrid, 2)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: ", surplus)
        TimescaleDb.write(conn, 'solar_kostal_surplus', surplus)
        
        Kostal.close(inverterclient)
        
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: " + str(round(consumption_total,2)) + ", generation: " + str(generation) + ", surplus: " + str(surplus) + ", powerToBattery: " + str(powerToBattery) + ", powerToGrid: " + str(powerToGrid))   
        
        # charger - we need to substract actual soyosource value
        valuesoyosource = TimescaleDb.read(conn, 'soyosource')
        chargersurplus = surplus - valuesoyosource

        chargerval = Charger(conn, tasmota_mqtt_name, chargersurplus, tasmota_charge_start, tasmota_charge_end)
        
        # idm
        idmval = Idm(conn, powerToGrid, feed_in_limit)

        # soyosource
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            surplus = 10000

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: " + str(surplus))  
        soyoval = TimescaleDb.increase(conn, 'soyosource', -surplus, float(maxOutput))
        TimescaleDb.write(conn, 'solar_soyosource', soyoval)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " soyoval: " + str(soyoval)) 

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charger: " + chargerval + ", iDM: " + str(idmval) + ", soyosource: " + str(round(soyoval,2)))  

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        if conn is not None:
            TimescaleDb.close(conn)
            #print('Database connection closed.')          
