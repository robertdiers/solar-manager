#!/usr/bin/env python

import pymodbus
import configparser
import os
import psycopg2
from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from urllib.request import urlopen

#read config
config = configparser.ConfigParser()

#-----------------------------------------
# Routine to read a float    
def ReadFloat(client,myadr_dec,unitid):
    r1=client.read_holding_registers(myadr_dec,2,unit=unitid)
    FloatRegister = BinaryPayloadDecoder.fromRegisters(r1.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    result_FloatRegister =round(FloatRegister.decode_32bit_float(),2)
    return(result_FloatRegister)   

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        inverter_ip = config['KostalSection']['inverter_ip']
        inverter_port = config['KostalSection']['inverter_port']
        
        #connection Kostal
        inverterclient = ModbusTcpClient(inverter_ip,port=inverter_port)            
        inverterclient.connect()       
        
        #all additional invertes will decrease my home consumption, so it might be negative - this is fine
        consumptionbat = ReadFloat(inverterclient,106,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption battery: ", consumptionbat)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_battery', consumptionbat)
        consumptiongrid = ReadFloat(inverterclient,108,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption grid: ", consumptiongrid)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_grid', consumptiongrid)
        consumptionpv = ReadFloat(inverterclient,116,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption pv: ", consumptionpv)
        #WriteTimescaleDb(conn, 'solar_kostal_consumption_pv', consumptionpv)
        consumption_total = consumptionbat + consumptiongrid + consumptionpv
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: ", consumption_total)
        
        inverter = ReadFloat(inverterclient,172,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter: ", inverter)   
        
        batteryamp = ReadFloat(inverterclient,200,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (A): ", batteryamp)
        batteryvolt = ReadFloat(inverterclient,216,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (V): ", batteryvolt)
        battery = round(batteryamp * batteryvolt, 2)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (W): ", battery)
        if batteryamp > 0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: discharge")
            powerToGrid = -1
        batterypercent = ReadFloat(inverterclient,210,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)
        
        #Kostal generation (by tracker/battery)
        dc1 = ReadFloat(inverterclient,260,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc1: ", dc1)
        #WriteTimescaleDb(conn, 'solar_kostal_generation_dc1', dc1)
        dc2 = ReadFloat(inverterclient,270,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc2: ", dc2)
        #WriteTimescaleDb(conn, 'solar_kostal_generation_dc2', dc2)
        dc3 = ReadFloat(inverterclient,280,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc3: ", dc3)
        #WriteTimescaleDb(conn, 'solar_kostal_generation_dc3', dc3)
        generation = round(dc1+dc2+dc3,2)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " generation: ", generation) 
        
        #this is not exact, but enough for us, wrong for negative consumption
        surplus = round(generation - consumption_total,1)

        # test values
        #surplus = -690

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: ", surplus)

        #this is not exact, but enough for us
        #powerToGrid = round(inverter - consumption_total,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        powerToGrid = -ReadFloat(inverterclient,252,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)   
        
        #we need to increase production if we use power from grid or battery
        soyodiff = battery + (-powerToGrid)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " soyodiff: ", soyodiff)

        inverterclient.close()
        
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: " + str(round(consumption_total,2)) + ", generation: " + str(generation) + ", surplus: " + str(surplus) + ", powerToGrid: " + str(powerToGrid))    

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex)       
