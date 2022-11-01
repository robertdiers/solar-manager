#!/usr/bin/env python

import pymodbus
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

#-----------------------------------------
# Routine to read a float    
def readfloat(client,myadr_dec,unitid):
    r1=client.read_holding_registers(myadr_dec,2,slave=unitid)
    FloatRegister = BinaryPayloadDecoder.fromRegisters(r1.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    result_FloatRegister =round(FloatRegister.decode_32bit_float(),2)
    return(result_FloatRegister)   

def read(inverter_ip, inverter_port):  
    try:

        #connection Kostal
        client = ModbusTcpClient(inverter_ip,port=inverter_port)            
        client.connect()

        result = {}

        #all additional invertes will decrease my home consumption, so it might be negative - this is fine
        consumptionbat = readfloat(client,106,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption battery: ", consumptionbat)
        result["consumptionbat"] = consumptionbat
        consumptiongrid = readfloat(client,108,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption grid: ", consumptiongrid)
        result["consumptiongrid"] = consumptiongrid
        consumptionpv = readfloat(client,116,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption pv: ", consumptionpv)
        result["consumptionpv"] = consumptionpv

        #CONSUMPTION WILL NOT GET NEGATIVE!
        consumption_total = consumptionbat + consumptiongrid + consumptionpv
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: ", consumption_total)
        result["consumption_total"] = consumption_total

        inverter = readfloat(client,172,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter: ", inverter)   
        result["inverter"] = inverter
        
        batteryamp = readfloat(client,200,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (A): ", batteryamp)
        result["batteryamp"] = batteryamp
        batteryvolt = readfloat(client,216,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (V): ", batteryvolt)
        result["batteryvolt"] = batteryvolt
        powerToBattery = -round(batteryamp * batteryvolt, 2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (W): ", battery)
        result["powerToBattery"] = powerToBattery
        if batteryamp > 0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: discharge")
            result["batteryflag"] = 0
        elif batteryamp < -0.1:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: charge")
            result["batteryflag"] = 1
        else:
            result["batteryflag"] = 0.5
        batterypercent = readfloat(client,210,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)
        result["batterypercent"] = batterypercent
        
        #Kostal generation (by tracker/battery)
        dc1 = readfloat(client,260,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc1: ", dc1)
        result["dc1"] = dc1
        dc2 = readfloat(client,270,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc2: ", dc2)
        result["dc2"] = dc2
        dc3 = readfloat(client,280,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc3: ", dc3)
        result["dc3"] = dc3
        generation = round(dc1+dc2+dc3,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " generation: ", generation) 
        result["generation"] = generation

        #this is not exact, but enough for us
        #powerToGrid = round(inverter - consumption_total,1)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        powerToGrid = -readfloat(client,252,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)  
        result["powerToGrid"] = powerToGrid

        #this is not exact, but enough for us, wrong for negative consumption
        #surplus = round(generation - consumption_total,1)
        # if we send power to battery or grid
        surplus = round(powerToBattery + powerToGrid, 2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: ", surplus)
        result["surplus"] = surplus
        
        dailyyield = round(readfloat(client,322,71) / 1000,2)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dailyyield: ", dailyyield)
        result["dailyyield"] = dailyyield
        
        return result      
    except Exception as ex:
        print ("ERROR Kostal: ", ex) 
    finally:
        client.close() 
      