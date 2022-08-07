#!/usr/bin/env python

import pymodbus
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

#-----------------------------------------
# Routine to read a float    
def readfloat(client,myadr_dec,unitid):
    r1=client.read_holding_registers(myadr_dec,2,unit=unitid)
    FloatRegister = BinaryPayloadDecoder.fromRegisters(r1.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    result_FloatRegister =round(FloatRegister.decode_32bit_float(),2)
    return(result_FloatRegister)   

#----------------------------------------- 
# Routine to write float
def writefloat(client,myadr_dec,feed_in,unitid):
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
    builder.add_32bit_float( feed_in )
    payload = builder.to_registers() 
    client.write_registers(myadr_dec, payload, unit=unitid)

def writeandread(idm_ip, idm_port, feed_in):  
    try:
        
        #connection iDM
        client = ModbusTcpClient(idm_ip,port=idm_port)     
        client.connect()  

        #solar power stored in 74
        writefloat(client,74,feed_in,1)
        return readfloat(client,74,1)
  
    except Exception as ex:
        print ("ERROR IDM: ", ex)
    finally:
        client.close() 
