#!/usr/bin/env python

from datetime import datetime

import TimescaleDb
import Tasmota
import BYD
import Config

# metrics from Tasmota
def tasmota(charge_mqtt_name, server_mqtt_name):
    try:
        result = Tasmota.get(server_mqtt_name, "8", ["StatusSNS_SI7021_Temperature"])
        TimescaleDb.write('technical_room_temperature', result["StatusSNS_SI7021_Temperature"])
    
        result = Tasmota.get(charge_mqtt_name, "8", ["StatusSNS_ENERGY_Power", "StatusSNS_ENERGY_Today"])
        TimescaleDb.write('solar_battery_charger_power', result["StatusSNS_ENERGY_Power"])
        TimescaleDb.write('solar_battery_charger_today', result["StatusSNS_ENERGY_Today"])
    except Exception as ex:
        print ("ERROR tasmota: ", ex)  

# metrics from BYD
def byd(byd_ip, byd_port):
    try:
        bydvalues = BYD.read(byd_ip, byd_port)
        TimescaleDb.write('solar_byd_soc', round(bydvalues["soc"]/100, 2))
        TimescaleDb.write('solar_byd_maxvolt', bydvalues["maxvolt"])
        TimescaleDb.write('solar_byd_minvolt', bydvalues["minvolt"])
        TimescaleDb.write('solar_byd_soh', round(bydvalues["soh"]/100, 2))
        TimescaleDb.write('solar_byd_maxtemp', bydvalues["maxtemp"])
        TimescaleDb.write('solar_byd_mintemp', bydvalues["mintemp"])
        TimescaleDb.write('solar_byd_battemp', bydvalues["battemp"])
        TimescaleDb.write('solar_byd_error', bydvalues["error"])
        TimescaleDb.write('solar_byd_power', bydvalues["power"])
        TimescaleDb.write('solar_byd_diffvolt', bydvalues["diffvolt"])
    except Exception as ex:
        print ("ERROR byd: ", ex)  

if __name__ == "__main__":  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        conf = Config.read()
        
        #connect interfaces
        TimescaleDb.connect(conf["timescaledb_ip"], conf["timescaledb_username"], conf["timescaledb_password"])
        Tasmota.connect(conf["mqtt_broker"], conf["mqtt_port"], conf["mqtt_user"], conf["mqtt_password"])

        #metrics
        tasmota(conf["charge_mqtt_name"], conf["server_mqtt_name"])
        byd(conf["byd_ip"], conf["byd_port"])

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()     