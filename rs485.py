#!/usr/bin/env python

import configparser
import os
import psycopg2
import serial
from datetime import datetime

#read config
config = configparser.ConfigParser()

# write metric to TimescaleDB
def WriteTimescaleDb(conn, table, value):
    # create a cursor
    cur = conn.cursor()   
    # execute a statement
    sql = 'insert into '+table+' (time, value) values (now(), %s)'
    cur.execute(sql, (value,))   
    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()

# write metric to TimescaleDB
def ReadTimescaleDb(conn, table):
    # create a cursor
    cur = conn.cursor()   
    # execute a statement
    sql = 'SELECT value FROM '+table+' where time = (select max(time) from '+table+')'
    cur.execute(sql)  
    row = cur.fetchone()
    value = row[0]
    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()
    return value

# Soyosource demand calculation
def computeDemand(sourceValue, maxOutput, numberOfUnits):
    if sourceValue > maxOutput: #if demand is higher than our max
        demand = maxOutput/numberOfUnits
        return int(demand) # s
    elif sourceValue >= (60*numberOfUnits): # if demand is above min 60 watts but less than max
        demand = sourceValue/numberOfUnits # this is to split the demand
        return int(demand) 
    elif sourceValue < (60*numberOfUnits): # if exporting or below min lets reduce the output to zero
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
def RS485(conn, rs485_device, numberOfUnits, maxOutput):
    try:
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
        tsdbval = 0 - ReadTimescaleDb(conn, 'solar_kostal_surplus')
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 tsdbval: ", tsdbval)
        demand = computeDemand(tsdbval, maxOutput, numberOfUnits)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 demand: ", demand)
        WriteTimescaleDb(conn, 'solar_soyosource', demand)

        # prepare packet and send        
        simulatedPacket = createPacket(demand, byte4, byte5, byte7)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 simulatedPacket: ", simulatedPacket)
        writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485: ", demand)
    except Exception as ex:
        print ("ERROR RS485: ", ex) 

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('rs485.ini')

        #read config and default values
        rs485_device = config['RS485Section']['rs485_device']  
        numberOfUnits = config['RS485Section']['numberOfUnits']  
        maxOutput = config['RS485Section']['maxOutput']  
        timescaledb_ip = config['MetricSection']['timescaledb_ip']
        timescaledb_username = config['MetricSection']['timescaledb_username']
        timescaledb_password = config['MetricSection']['timescaledb_password']

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
        
        #init Timescaledb
        conn = psycopg2.connect(
            host=timescaledb_ip,
            database="postgres",
            user=timescaledb_username,
            password=timescaledb_password)        

        # RS485 Soyosource
        RS485(conn, rs485_device, float(numberOfUnits), float(maxOutput))

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        if conn is not None:
            conn.close()
            #print('Database connection closed.')          
