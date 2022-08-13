#!/usr/bin/env python

from datetime import datetime

import TimescaleDb
import IdmPump
import Kostal
import Tasmota
import Config

# charger
def charger(charger_mqtt_name, surplus, charge_start, charge_end):
    try:
        retval = 'ON'

        #we will always charge between 12:00 and 12:05 to ensure a kind of "battery protect"
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            Tasmota.on(charger_mqtt_name)
            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging battery protect: ", surplus)
            TimescaleDb.write('solar_battery_chargestatus', 1)
            retval = 'ON'
        else:
            if surplus > int(charge_start):
                Tasmota.on(charger_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger start charging: ", surplus)
                TimescaleDb.write('solar_battery_chargestatus', 1)
                retval = 'ON'
            elif surplus < int(charge_end):
                Tasmota.off(charger_mqtt_name)
                #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " Charger stop charging: ", surplus)
                TimescaleDb.write('solar_battery_chargestatus', 0)   
                retval = 'OFF'
            else:
                TimescaleDb.write('solar_battery_chargestatus', 0.5) 
                retval = 'UNCHANGED'
        
        return retval
    except Exception as ex:
        print ("ERROR charger: ", ex)  

# idm heat pump
def idm(idm_ip, idm_port, powerToGrid, feed_in_limit):
    try: 
        #feed in must be above our limit
        feed_in = powerToGrid
        if feed_in > feed_in_limit:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM feed-in reached: ", feed_in)               
            feed_in = feed_in/1000
        else:
            #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " iDM send ZERO: ", feed_in)  
            feed_in = 0
            
        TimescaleDb.write('solar_idm_feedin', (feed_in*1000))

        #connection iDM
        return IdmPump.writeandread(idm_ip, idm_port, feed_in)
    except Exception as ex:
        print ("ERROR idm: ", ex)  

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        conf = Config.read()
        
        #connect interfaces
        TimescaleDb.connect(conf["timescaledb_ip"], conf["timescaledb_username"], conf["timescaledb_password"])
        Tasmota.connect(conf["mqtt_broker"], conf["mqtt_port"], conf["mqtt_user"], conf["mqtt_password"])

        #read Kostal
        kostalvalues = Kostal.read(conf["inverter_ip"], conf["inverter_port"])
        TimescaleDb.write('solar_kostal_consumption_total', kostalvalues["consumption_total"])
        TimescaleDb.write('solar_kostal_inverter', kostalvalues["inverter"])
        TimescaleDb.write('solar_kostal_batteryflag', kostalvalues["batteryflag"])
        TimescaleDb.write('solar_kostal_batterypercent', (kostalvalues["batterypercent"]/100))
        TimescaleDb.write('solar_kostal_generation_total', kostalvalues["generation"]) 
        TimescaleDb.write('solar_kostal_powertogrid', kostalvalues["powerToGrid"])
        TimescaleDb.write('solar_kostal_surplus', kostalvalues["surplus"])
        TimescaleDb.write('solar_kostal_dailyyield', kostalvalues["dailyyield"])
         
        # charger - we need to substract actual soyosource value
        surplus = kostalvalues["surplus"]
        valuesoyosource = TimescaleDb.read('soyosource')
        chargersurplus = surplus - valuesoyosource

        chargerval = charger(conf["charge_mqtt_name"], chargersurplus, conf["charge_start"], conf["charge_end"])
        
        # idm
        idmval = idm(conf["idm_ip"], conf["idm_port"], kostalvalues["powerToGrid"], conf["feed_in_limit"])

        # soyosource should not use battery during this time
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            surplus = 10000

        #store value for soyosource rs485 script
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: " + str(surplus))  
        soyoval = TimescaleDb.increase('soyosource', -surplus, conf["maxOutput"])
        TimescaleDb.write('solar_soyosource', soyoval)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " soyoval: " + str(soyoval)) 

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: " + str(round(kostalvalues["consumption_total"],2)) + ", generation: " + str(kostalvalues["generation"]) + ", surplus: " + str(kostalvalues["surplus"]) + ", powerToBattery: " + str(kostalvalues["powerToBattery"]) + ", powerToGrid: " + str(kostalvalues["powerToGrid"]) + ", charger: " + chargerval + ", iDM: " + str(idmval) + ", soyosource: " + str(round(soyoval,2)))  

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()     
