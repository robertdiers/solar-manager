#!/usr/bin/env python

import pymodbus
import configparser
import os
from datetime import datetime
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

#read config
config = configparser.ConfigParser()
client = "unknown"

#-----------------------------------------
# Routine to read a float    
def readfloat(myadr_dec,unitid):
    global client
    r1=client.read_holding_registers(myadr_dec,2,unit=unitid)
    FloatRegister = BinaryPayloadDecoder.fromRegisters(r1.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    result_FloatRegister =round(FloatRegister.decode_32bit_float(),2)
    return(result_FloatRegister)   

#----------------------------------------- 
# Routine to write float
def writefloat(myadr_dec,feed_in,unitid):
    global client
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
    builder.add_32bit_float( feed_in )
    payload = builder.to_registers() 
    client.write_registers(myadr_dec, payload, unit=unitid)

def connect():  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        inverter_ip = config['KostalSection']['inverter_ip']
        inverter_port = config['KostalSection']['inverter_port']

        # override with environment variables
        if os.getenv('INVERTER_IP','None') != 'None':
            inverter_ip = os.getenv('INVERTER_IP')
            print ("using env: INVERTER_IP")
        if os.getenv('INVERTER_PORT','None') != 'None':
            inverter_port = os.getenv('INVERTER_PORT')
            print ("using env: INVERTER_PORT")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_ip: ", inverter_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_port: ", inverter_port)

        #connection Kostal
        global client
        client = ModbusTcpClient(inverter_ip,port=inverter_port)            
        client.connect()
      
    except Exception as ex:
        print ("ERROR: ", ex) 

def close():    
    global client
    client.close()   
