#!/usr/bin/env python

import socket

BUFFER_SIZE = 1024
MESSAGE_1 = "010300000066c5e0" #read serial
MESSAGE_2 = "01030500001984cc" #read data

def buf2int16SI(byteArray, pos): #signed
    result = byteArray[pos] * 256 + byteArray[pos + 1]
    if (result > 32768):
        result -= 65536
    return result

def buf2int16US(byteArray, pos): #unsigned
    result = byteArray[pos] * 256 + byteArray[pos + 1]
    return result

def read(byd_ip, byd_port):  
    try:
        
        #connection BYD
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((byd_ip, byd_port))

        #message 1
        #client.send(bytes.fromhex(MESSAGE_1))

        #read serial
        #data = client.recv(BUFFER_SIZE)
        #print (data.hex())
        #serial = ""
        #for x in range(3, 22):
        #    serial += chr(data[x])
        #print (serial)  

        #message 2
        client.send(bytes.fromhex(MESSAGE_2))

        #read data
        data = client.recv(BUFFER_SIZE)
        #print (data.hex())
        soc = buf2int16SI(data, 3)
        #print ("soc: "+str(soc))
        maxvolt = buf2int16SI(data, 5) * 1.0 / 100.0
        #print ("maxvolt: "+str(maxvolt))
        minvolt = buf2int16SI(data, 7) * 1.0 / 100.0
        #print ("minvolt: "+str(minvolt))
        soh = buf2int16SI(data, 9)
        #print ("soh: "+str(soh))
        ampere = buf2int16SI(data, 11) * 1.0 / 10.0
        #print ("ampere: "+str(ampere))
        battvolt = buf2int16US(data, 13) * 1.0 / 100.0
        #print ("battvolt: "+str(battvolt))
        maxtemp = buf2int16SI(data, 15)
        #print ("maxtemp: "+str(maxtemp))
        mintemp = buf2int16SI(data, 17)
        #print ("mintemp: "+str(mintemp))
        battemp = buf2int16SI(data, 19)
        #print ("battemp: "+str(battemp))
        error = buf2int16SI(data, 29)
        #print ("error: "+str(error))
        paramt = chr(data[31]) + "." + chr(data[32])
        #print ("paramt: "+str(paramt))
        outvolt = buf2int16US(data, 35) * 1.0 / 100.0
        #print ("outvolt: "+str(outvolt))
        power = round((ampere * outvolt) * 100 / 100, 2)
        #print ("power: "+str(power))
        diffvolt = round((maxvolt - minvolt) * 100 / 100, 2)
        #print ("diffvolt: "+str(diffvolt))

        client.close()

        return {
            "soc": soc,
            "maxvolt": maxvolt,
            "minvolt": minvolt,
            "soh": soh,
            "ampere": ampere,
            "battvolt": battvolt,
            "maxtemp": maxtemp,
            "mintemp": mintemp,
            "battemp": battemp,
            "error": error,
            "paramt": paramt,
            "outvolt": outvolt,
            "power": power,
            "diffvolt": diffvolt,
        }
      
    except Exception as ex:
        print ("ERROR BYD: ", ex)
