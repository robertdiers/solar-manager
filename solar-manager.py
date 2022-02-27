#!/usr/bin/env python

import pymodbus
import configparser
import os
import psycopg2
import serial
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
#----------------------------------------- 
# Routine to write float
def WriteFloat(client,myadr_dec,feed_in,unitid):
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
    builder.add_32bit_float( feed_in )
    payload = builder.to_registers() 
    client.write_registers(myadr_dec, payload, unit=unitid)

# read status from Tasmota
def StatusTasmota(tasmotaip):
    if not tasmotaip:
        return 'DISABLED'
    try:
        statuslink = urlopen('http://'+tasmotaip+'/?m=1')
        return statuslink.read().decode('utf-8')
    except Exception as e:
        print (e)
        return 'ERROR'

# set status Tasmota
def SwitchTasmota(tasmotaip, status):
    print (tasmotaip+' '+status)
    try:
        if 'ON' in status and 'OFF' in StatusTasmota(tasmotaip):
            switchlink = urlopen('http://'+tasmotaip+'/?m=1&o=1')
            retval = switchlink.read().decode('utf-8')
            print(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + tasmotaip + ': ' + retval)
        if 'OFF' in status and 'ON' in StatusTasmota(tasmotaip):
            switchlink = urlopen('http://'+tasmotaip+'/?m=1&o=1')
            retval = switchlink.read().decode('utf-8')
            print(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + ' ' + tasmotaip + ': ' + retval)
    except Exception as e:
        print (e)

# write metric to TimescaleDB
def WriteTimescaleDb(conn, table, value):
    if conn:
        # create a cursor
        cur = conn.cursor()   
        # execute a statement
        sql = 'insert into '+table+' (time, value) values (now(), %s)'
        cur.execute(sql, (value,))   
        # commit the changes to the database
        conn.commit()
        # close the communication with the PostgreSQL
        cur.close()

# charger
def Charger(conn, tasmota_charge_ip, surplus, tasmota_charge_start, tasmota_charge_end):
    try:
        #charging
        chargestatus = StatusTasmota(tasmota_charge_ip)
        if 'ON' in chargestatus:
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger chargestatus: ", 'ON')
            WriteTimescaleDb(conn, 'solar_battery_chargestatus', 1)
        if 'OFF' in chargestatus:
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger chargestatus: ", 'OFF')
            WriteTimescaleDb(conn, 'solar_battery_chargestatus', 0)

        #we will always charge between 12:00 and 12:05 to ensure a kind of "battery protect"
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            if 'OFF' in chargestatus:
                SwitchTasmota(tasmota_charge_ip, 'ON')
                print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging battery protect: ", surplus)
                WriteTimescaleDb(conn, 'solar_battery_chargestatus', 1)
        else:
            if 'OFF' in chargestatus and surplus > int(tasmota_charge_start):
                SwitchTasmota(tasmota_charge_ip, 'ON')
                print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging: ", surplus)
                WriteTimescaleDb(conn, 'solar_battery_chargestatus', 1)
            if 'ON' in chargestatus and surplus < int(tasmota_charge_end):
                SwitchTasmota(tasmota_charge_ip, 'OFF')
                print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger stop charging: ", surplus)
                WriteTimescaleDb(conn, 'solar_battery_chargestatus', 0)   
    except Exception as ex:
        print ("ERROR Charger: ", ex)  

# idm heat pump
def Idm(conn, powerToGrid, feed_in_limit, idm_ip, idm_port):
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
        idmclient = ModbusTcpClient(idm_ip,port=idm_port)            
        idmclient.connect()        
       
        WriteFloat(idmclient,74,feed_in,1)
        WriteTimescaleDb(conn, 'solar_idm_feedin', (feed_in*1000))
            
        #read from iDM
        idmvalue = ReadFloat(idmclient,74,1)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM: ", idmvalue)
            
        idmclient.close()   
    except Exception as ex:
        print ("ERROR Idm: ", ex) 

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
def RS485(conn, rs485_device, surplus, numberOfUnits, maxOutput):
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

        # above zero means generation > consumption
        if (surplus > 0):
            surplus = 0
        surplus = -surplus

        # we can calculate the demand
        demand = computeDemand(surplus, maxOutput, numberOfUnits)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 demand: ", demand)
        WriteTimescaleDb(conn, 'solar_soyosource', demand)

        # prepare packet and send        
        simulatedPacket = createPacket(demand, byte4, byte5, byte7)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485 simulatedPacket: ", simulatedPacket)
        writeToSerial(simulatedPacket, serialWrite, byte0, byte1, byte2, byte3, byte6)

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " RS485: ", demand)
    except Exception as ex:
        print ("ERROR RS485: ", ex) 

if __name__ == "__main__":  
    print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager-defaults.ini')
        config.read('solar-manager.ini')

        #read config and default values
        inverter_ip = config['KostalSection']['inverter_ip']
        inverter_port = config['KostalSection']['inverter_port']
        idm_ip = config['IdmSection']['idm_ip']
        idm_port = config['IdmSection']['idm_port']  
        feed_in_limit = int(config['IdmSection']['feed_in_limit']) 
        tasmota_charge_ip = config['ChargerSection']['tasmota_charge_ip']
        tasmota_charge_start = config['ChargerSection']['tasmota_charge_start']  
        tasmota_charge_end = config['ChargerSection']['tasmota_charge_end']  
        rs485_device = config['RS485Section']['rs485_device']  
        numberOfUnits = config['RS485Section']['numberOfUnits']  
        maxOutput = config['RS485Section']['maxOutput']  
        timescaledb_ip = config['MetricSection']['timescaledb_ip']
        timescaledb_username = config['MetricSection']['timescaledb_username']
        timescaledb_password = config['MetricSection']['timescaledb_password']

        # override with environment variables
        if os.getenv('INVERTER_IP','None') != 'None':
            inverter_ip = os.getenv('INVERTER_IP')
            print ("using env: INVERTER_IP")
        if os.getenv('INVERTER_PORT','None') != 'None':
            inverter_port = os.getenv('INVERTER_PORT')
            print ("using env: INVERTER_PORT")
        if os.getenv('IDM_IP','None') != 'None':
            idm_ip = os.getenv('IDM_IP')
            print ("using env: IDM_IP")
        if os.getenv('IDM_PORT','None') != 'None':
            idm_port = os.getenv('IDM_PORT')
            print ("using env: IDM_PORT")
        if os.getenv('FEED_IN_LIMIT','None') != 'None':
            feed_in_limit = os.getenv('FEED_IN_LIMIT')
            print ("using env: FEED_IN_LIMIT")
        if os.getenv('TASMOTA_CHARGE_IP','None') != 'None':
            tasmota_charge_ip = os.getenv('TASMOTA_CHARGE_IP')
            print ("using env: TASMOTA_CHARGE_IP")
        if os.getenv('TASMOTA_CHARGE_START','None') != 'None':
            tasmota_charge_start = os.getenv('TASMOTA_CHARGE_START')
            print ("using env: TASMOTA_CHARGE_START")
        if os.getenv('TASMOTA_CHARGE_END','None') != 'None':
            tasmota_charge_end = os.getenv('TASMOTA_CHARGE_END')
            print ("using env: TASMOTA_CHARGE_END")
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

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_ip: ", inverter_ip)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_port: ", inverter_port)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_ip: ", idm_ip)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_port: ", idm_port)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " feed_in_limit: ", feed_in_limit)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_charge_ip: ", tasmota_charge_ip)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_charge_start: ", tasmota_charge_start)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_charge_end: ", tasmota_charge_end)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " rs485_device: ", rs485_device)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " numberOfUnits: ", numberOfUnits)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " maxOutput: ", maxOutput)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_ip: ", timescaledb_ip)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_username: ", timescaledb_username)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_password: ", timescaledb_password)
        
        #init Timescaledb if used
        if timescaledb_ip:
            conn = psycopg2.connect(
                host=timescaledb_ip,
                database="postgres",
                user=timescaledb_username,
                password=timescaledb_password)

        #connection Kostal
        inverterclient = ModbusTcpClient(inverter_ip,port=inverter_port)            
        inverterclient.connect()       
        
        #all additional invertes will decrease my home consumption, so it might be negative - this is fine
        consumptionbat = ReadFloat(inverterclient,106,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption battery: ", consumptionbat)
        WriteTimescaleDb(conn, 'solar_kostal_consumption_battery', consumptionbat)
        consumptiongrid = ReadFloat(inverterclient,108,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption grid: ", consumptiongrid)
        WriteTimescaleDb(conn, 'solar_kostal_consumption_grid', consumptiongrid)
        consumptionpv = ReadFloat(inverterclient,116,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption pv: ", consumptionpv)
        WriteTimescaleDb(conn, 'solar_kostal_consumption_pv', consumptionpv)
        consumption_total = consumptionbat + consumptiongrid + consumptionpv
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: ", consumption_total)
        WriteTimescaleDb(conn, 'solar_kostal_consumption_total', consumption_total)

        inverter = ReadFloat(inverterclient,172,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter: ", inverter)   
        WriteTimescaleDb(conn, 'solar_kostal_inverter', inverter)
        
        batteryamp = ReadFloat(inverterclient,200,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (A): ", batteryamp)
        batteryvolt = ReadFloat(inverterclient,216,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (V): ", batteryvolt)
        battery = round(batteryamp * batteryvolt, 2)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (W): ", battery)
        WriteTimescaleDb(conn, 'solar_kostal_battery', battery)
        if batteryamp > 0.1:
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery: discharge")
            powerToGrid = -1
            WriteTimescaleDb(conn, 'solar_kostal_batteryflag', 1)
        elif batteryamp < -0.1:
            WriteTimescaleDb(conn, 'solar_kostal_batteryflag', -1)
        else:
            WriteTimescaleDb(conn, 'solar_kostal_batteryflag', 0)
        batterypercent = ReadFloat(inverterclient,210,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)
        WriteTimescaleDb(conn, 'solar_kostal_batterypercent', (batterypercent/100))
        
        #Kostal generation (by tracker/battery)
        dc1 = ReadFloat(inverterclient,260,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc1: ", dc1)
        WriteTimescaleDb(conn, 'solar_kostal_generation_dc1', dc1)
        dc2 = ReadFloat(inverterclient,270,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc2: ", dc2)
        WriteTimescaleDb(conn, 'solar_kostal_generation_dc2', dc2)
        dc3 = ReadFloat(inverterclient,280,71)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " dc3: ", dc3)
        WriteTimescaleDb(conn, 'solar_kostal_generation_dc3', dc3)
        generation = round(dc1+dc2+dc3,2)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " generation: ", generation) 
        WriteTimescaleDb(conn, 'solar_kostal_generation_total', generation)
        
        #this is not exact, but enough for us
        surplus = round(generation - consumption_total,1)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: ", surplus)
        WriteTimescaleDb(conn, 'solar_kostal_surplus', surplus)

        #this is not exact, but enough for us
        powerToGrid = round(inverter - consumption_total,1)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " powerToGrid: ", powerToGrid)   
        WriteTimescaleDb(conn, 'solar_kostal_powertogrid', powerToGrid)
        
        inverterclient.close()

        # test values
        surplus = -900
        
        # charger
        Charger(conn, tasmota_charge_ip, surplus, tasmota_charge_start, tasmota_charge_end)
        
        # idm
        Idm(conn, powerToGrid, feed_in_limit, idm_ip, idm_port)

        # RS485 Soyosource
        RS485(conn, rs485_device, surplus, float(numberOfUnits), float(maxOutput))

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')          
