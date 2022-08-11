#!/usr/bin/env python

from datetime import datetime
import time

import Config
import Daly
import TimescaleDb

#define interesting attributes        
attributes = ["Pack_Voltage", "Pack_Current", "Pack_SOC", "Pack_Cycles", "Pack_MinTemperature", "Pack_MaxTemperature", "Pack_High CellV", "Pack_Low CellV", "Pack_Cell Difference"]
#my blocks have 16 cells
for x in range(16):
    attributes.append("CellV_CellV "+str(x))

def writedb(name, json):
    #print (json)
    global attributes
    for attribute in attributes:
        #print(attribute)
        if attribute in json:
            #print(attribute+": "+str(json[attribute]))
            TimescaleDb.write(name+'_'+attribute, float(json[attribute]))

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

        #run open end
        waitflag = 'true'
        while (waitflag):
            time.sleep(60)
            waitflag = 'true'
            #print ("waiting")

    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()
        Daly.close(daly1, conf["daly1_mqtt_name"])
        Daly.close(daly2, conf["daly2_mqtt_name"])
        Daly.close(daly3, conf["daly3_mqtt_name"])
