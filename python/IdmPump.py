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
        idm_ip = config['IdmSection']['idm_ip']
        idm_port = config['IdmSection']['idm_port']  

        # override with environment variables
        if os.getenv('IDM_IP','None') != 'None':
            idm_ip = os.getenv('IDM_IP')
            print ("using env: IDM_IP")
        if os.getenv('IDM_PORT','None') != 'None':
            idm_port = os.getenv('IDM_PORT')
            print ("using env: IDM_PORT")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_ip: ", idm_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_port: ", idm_port)           
        
        #connection iDM
        global client
        client = ModbusTcpClient(idm_ip,port=idm_port)     
        client.connect()  
  
    except Exception as ex:
        print ("ERROR: ", ex)

def close():
    global client
    client.close()  
