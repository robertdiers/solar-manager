#!/usr/bin/env python

import configparser
import os
import serial
import time
from datetime import datetime

import TimescaleDb

#read config
config = configparser.ConfigParser()

# Soyosource demand calculation
def computeDemand(sourceValue, maxOutput, numberOfUnits):
    if sourceValue > maxOutput: #if demand is higher than our max
        demand = maxOutput/numberOfUnits
        return int(demand) # s
    elif sourceValue > 0: # if demand is above 0 but less than max
        demand = sourceValue/numberOfUnits # this is to split the demand
        return int(demand) 
    elif sourceValue <= 0: # if exporting lets reduce the output to zero
        demand = 0
        return int(demand) # only demand is required but value is for logs
    else:
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " computeDemand invalid source value: ", sourceValue)

# Soyosource packet creation
def createPacket(demand, byte4, byte5, byte7):
    byte4 = int(demand/256) ## (2 byte watts as short integer xaxb)
    if byte4 < 0 or byte4 > 256:
        byte4 = 0
    byte5 = int(demand)-(byte4 * 256) ## (2 byte watts as short integer xaxb)
    if byte5 < 0 or byte5 > 256:
        byte5 = 0
    byte7 = (264 - byte4 - byte5) #checksum calculation
    if byte7 > 256:
        byte7 = 8
    return byte4, byte5, byte7

# Soyosource write to RS-485
def writeToSerial(packet, serialWrite, byte0, byte1, byte2, byte3, byte6):
    try:
        packet = [byte0,byte1,byte2,byte3,packet[0],packet[1],byte6,packet[2]]
        serialWrite.write(bytearray(packet))
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " complete decimal packet: s%", packet)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " raw bytearray packet being sent to serial: %s", bytearray(packet))
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " checksum calc= %s", 264-packet[0]-packet[1])
    except Exception as ex:
        print ("ERROR writeToSerial: ", ex)
    return packet

# idm heat pump
def RS485(rs485_device, numberOfUnits, maxOutput):
    actualsec = datetime.now().strftime("%S")
    #print ('###' + actualsec)

    ## CREATE GLOBALS
    byte0 = 36
    byte1 = 86
    byte2 = 0
    byte3 = 33
    byte4 = 0 ##(2 byte watts as short integer xaxb)
    byte5 = 0 ##(2 byte watts as short integer xaxb)
    byte6 = 128
    byte7 = 8 ## checksum
    packet = [byte0,byte1,byte2,byte3,byte4,byte5,byte6,byte7]
    serialWrite = serial.Serial(rs485_device, 4800, timeout=1) # define serial port on which to output RS485 data

    # we will send the demand from Timescaledb
    tsdbval = TimescaleDb.read('soyosource')
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 tsdbval: ", tsdbval)
    demand = computeDemand(tsdbval, maxOutput, numberOfUnits)
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 demand: ", demand)
    TimescaleDb.write('solar_soyosource_inverter', demand)

    # prepare packet      
    simulatedPacket = createPacket(demand, byte4, byte5, byte7)
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 simulatedPacket: ", simulatedPacket)

    # send package 5 times, every 2 sec (in 10 sec time window)
    writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)
    time.sleep(2)
    writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)
    time.sleep(2)
    writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)
    time.sleep(2)
    writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)
    time.sleep(2)
    writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        rs485_device = config['RS485Section']['rs485_device']  
        numberOfUnits = config['RS485Section']['numberOfUnits']  
        maxOutput = config['RS485Section']['maxOutput']  

        timescaledb_ip = config['DatabaseSection']['timescaledb_ip']
        timescaledb_username = config['DatabaseSection']['timescaledb_username']
        timescaledb_password = config['DatabaseSection']['timescaledb_password']

        # override with environment variables        
        if os.getenv('RS485_DEVICE','None') != 'None':
            rs485_device = os.getenv('RS485_DEVICE')
            print ("using env: RS485_DEVICE")
        if os.getenv('NUMBEROFUNITS','None') != 'None':
            numberOfUnits = os.getenv('NUMBEROFUNITS')
            print ("using env: NUMBEROFUNITS")
        if os.getenv('MAXOUTPUT','None') != 'None':
            maxOutput = os.getenv('MAXOUTPUT')
            print ("using env: MAXOUTPUT")

        if os.getenv('TIMESCALEDB_IP','None') != 'None':
            timescaledb_ip = os.getenv('TIMESCALEDB_IP')
            print ("using env: TIMESCALEDB_IP")
        if os.getenv('TIMESCALEDB_USERNAME','None') != 'None':
            timescaledb_username = os.getenv('TIMESCALEDB_USERNAME')
            print ("using env: TIMESCALEDB_USERNAME")
        if os.getenv('TIMESCALEDB_PASSWORD','None') != 'None':
            timescaledb_password = os.getenv('TIMESCALEDB_PASSWORD')
            print ("using env: TIMESCALEDB_PASSWORD")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " rs485_device: ", rs485_device)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " numberOfUnits: ", numberOfUnits)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " maxOutput: ", maxOutput)   

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_ip: ", timescaledb_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_username: ", timescaledb_username)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_password: ", timescaledb_password)

        #connect once every 10 sec and not every 2 sec...
        TimescaleDb.connect(timescaledb_ip, timescaledb_username, timescaledb_password)

        # RS485 Soyosource
        RS485(rs485_device, float(numberOfUnits), float(maxOutput))

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR rs485: ", ex) 
    finally:
        TimescaleDb.close()        
