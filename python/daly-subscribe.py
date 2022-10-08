#!/usr/bin/env python

from datetime import datetime
import time
import math

import Config
import Daly
import TimescaleDb

#define interesting attributes        
attributes = ["Pack_Voltage", "Pack_Current", "Pack_SOC", "Pack_Cycles", "Pack_High_CellV", "Pack_Low_CellV", "Pack_Cell_Diff", "Pack_Cell_Temp", "Pack_BMS_Temp"]
#max 48 blocks
for x in range(48):
    attributes.append("CellV_CellV "+str(x))

def writedb(name, json):
    #print (json)
    global attributes
    for attribute in attributes:
        #print(attribute)
        if attribute in json:
            #print(attribute+": "+str(json[attribute]))
            value = 0
            if math.isnan(value):
                print(attribute+" nan: "+str(json[attribute]))
            else:
                value = float(json[attribute])
                if attribute in 'Pack_Cell_Diff':
                    value = value / 1000.0
                    #print (value)
                if attribute in 'Pack_SOC':
                    value = value / 100.0
                    #print (value)
                if attribute in 'Pack_Current':
                    value = value * float(json['Pack_Voltage'])
                    #print (value)
                if attribute.startswith('CellV_CellV'):
                    TimescaleDb.writeV(name+'_'+attribute, value)
                else:
                    TimescaleDb.write(name+'_'+attribute, value)

if __name__ == "__main__":  
    daly1 = ''
    daly2 = ''
    daly3 = ''
    conf = Config.read()
    try:

        TimescaleDb.connect(conf["timescaledb_ip"], conf["timescaledb_username"], conf["timescaledb_password"])
        
        #subscribe all Daly
        daly1 = Daly.subscribe(conf["mqtt_broker"], conf["mqtt_port"], conf["mqtt_user"], conf["mqtt_password"], conf["daly1_mqtt_name"], writedb, "Daly1")
        daly2 = Daly.subscribe(conf["mqtt_broker"], conf["mqtt_port"], conf["mqtt_user"], conf["mqtt_password"], conf["daly2_mqtt_name"], writedb, "Daly2")
        daly3 = Daly.subscribe(conf["mqtt_broker"], conf["mqtt_port"], conf["mqtt_user"], conf["mqtt_password"], conf["daly3_mqtt_name"], writedb, "Daly3")

        #run 10 minutes
        minutes = 0
        while (minutes < 10):
            time.sleep(60)
            minutes = minutes + 1
            #print ("waiting")

    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()
        Daly.close(daly1, conf["daly1_mqtt_name"])
        Daly.close(daly2, conf["daly2_mqtt_name"])
        Daly.close(daly3, conf["daly3_mqtt_name"])
