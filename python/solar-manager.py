#!/usr/bin/env python

import configparser
import os
from datetime import datetime
from urllib.request import urlopen

import TimescaleDb
import IdmPump
import Kostal
import Tasmota
import BYD

#read config
config = configparser.ConfigParser()

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
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        idm_ip = config['IdmSection']['idm_ip']
        idm_port = config['IdmSection']['idm_port']  
        feed_in_limit = int(config['IdmSection']['feed_in_limit']) 

        charge_start = config['ChargerSection']['charge_start']  
        charge_end = config['ChargerSection']['charge_end']  
        charge_mqtt_name = config['ChargerSection']['charge_mqtt_name']

        server_mqtt_name = config['ServerSection']['server_mqtt_name']

        maxOutput = config['RS485Section']['maxOutput']

        timescaledb_ip = config['DatabaseSection']['timescaledb_ip']
        timescaledb_username = config['DatabaseSection']['timescaledb_username']
        timescaledb_password = config['DatabaseSection']['timescaledb_password']

        mqtt_broker = config['MqttSection']['mqtt_broker']
        mqtt_port = config['MqttSection']['mqtt_port']
        mqtt_user = config['MqttSection']['mqtt_user']
        mqtt_password = config['MqttSection']['mqtt_password']

        inverter_ip = config['KostalSection']['inverter_ip']
        inverter_port = config['KostalSection']['inverter_port']

        byd_ip = config['BydSection']['byd_ip']
        byd_port = config['BydSection']['byd_port']

        # override with environment variables
        if os.getenv('IDM_IP','None') != 'None':
            idm_ip = os.getenv('IDM_IP')
            print ("using env: IDM_IP")
        if os.getenv('IDM_PORT','None') != 'None':
            idm_port = os.getenv('IDM_PORT')
            print ("using env: IDM_PORT")
        if os.getenv('FEED_IN_LIMIT','None') != 'None':
            feed_in_limit = os.getenv('FEED_IN_LIMIT')
            print ("using env: FEED_IN_LIMIT")

        if os.getenv('CHARGE_START','None') != 'None':
            charge_start = os.getenv('CHARGE_START')
            print ("using env: CHARGE_START")
        if os.getenv('CHARGE_END','None') != 'None':
            charge_end = os.getenv('CHARGE_END')
            print ("using env: CHARGE_END")
        if os.getenv('CHARGE_MQTT_NAME','None') != 'None':
            charge_mqtt_name = os.getenv('CHARGE_MQTT_NAME')
            print ("using env: CHARGE_MQTT_NAME")
        
        if os.getenv('SERVER_MQTT_NAME','None') != 'None':
            server_mqtt_name = os.getenv('SERVER_MQTT_NAME')
            print ("using env: SERVER_MQTT_NAME")
        
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
        
        if os.getenv('MQTT_BROKER','None') != 'None':
            mqtt_broker = os.getenv('MQTT_BROKER')
            print ("using env: MQTT_BROKER")
        if os.getenv('MQTT_PORT','None') != 'None':
            mqtt_port = os.getenv('MQTT_PORT')
            print ("using env: MQTT_PORT")
        if os.getenv('MQTT_USER','None') != 'None':
            mqtt_user = os.getenv('MQTT_USER')
            print ("using env: MQTT_USER")
        if os.getenv('MQTT_PASSWORD','None') != 'None':
            mqtt_password = os.getenv('MQTT_PASSWORD')
            print ("using env: MQTT_PASSWORD")
        
        if os.getenv('INVERTER_IP','None') != 'None':
            inverter_ip = os.getenv('INVERTER_IP')
            print ("using env: INVERTER_IP")
        if os.getenv('INVERTER_PORT','None') != 'None':
            inverter_port = os.getenv('INVERTER_PORT')
            print ("using env: INVERTER_PORT")
        
        if os.getenv('BYD_IP','None') != 'None':
            byd_ip = os.getenv('BYD_IP')
            print ("using env: BYD_IP")
        if os.getenv('BYD_PORT','None') != 'None':
            byd_port = os.getenv('BYD_PORT')
            print ("using env: BYD_PORT")
        
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_ip: ", idm_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " idm_port: ", idm_port)     
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " feed_in_limit: ", feed_in_limit)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_start: ", charge_start)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_end: ", charge_end)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " charge_mqtt_name: ", charge_mqtt_name) 

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " server_mqtt_name: ", server_mqtt_name) 

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " maxOutput: ", maxOutput)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_ip: ", timescaledb_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_username: ", timescaledb_username)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_password: ", timescaledb_password)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_broker: ", mqtt_broker)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_port: ", mqtt_port)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_user: ", mqtt_user)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_password: ", mqtt_password)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_ip: ", inverter_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " inverter_port: ", inverter_port)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " byd_ip: ", byd_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " byd_port: ", byd_port)
        
        #connect interfaces
        TimescaleDb.connect(timescaledb_ip, timescaledb_username, timescaledb_password)
        Tasmota.connect(mqtt_broker, mqtt_port, mqtt_user, mqtt_password)

        #read Kostal
        kostalvalues = Kostal.read(inverter_ip, inverter_port)
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

        chargerval = charger(charge_mqtt_name, chargersurplus, charge_start, charge_end)
        
        # idm
        idmval = idm(idm_ip, idm_port, kostalvalues["powerToGrid"], feed_in_limit)

        # soyosource should not use battery during this time
        now = datetime.now()
        if now.hour == 12 and now.minute < 5:
            surplus = 10000

        #store value for soyosource rs485 script
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " surplus: " + str(surplus))  
        soyoval = TimescaleDb.increase('soyosource', -surplus, float(maxOutput))
        TimescaleDb.write('solar_soyosource', soyoval)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " soyoval: " + str(soyoval)) 

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " consumption: " + str(round(kostalvalues["consumption_total"],2)) + ", generation: " + str(kostalvalues["generation"]) + ", surplus: " + str(kostalvalues["surplus"]) + ", powerToBattery: " + str(kostalvalues["powerToBattery"]) + ", powerToGrid: " + str(kostalvalues["powerToGrid"]) + ", charger: " + chargerval + ", iDM: " + str(idmval) + ", soyosource: " + str(round(soyoval,2)))  
    
        # metrics
        tasmota(charge_mqtt_name, server_mqtt_name)
        byd(byd_ip, byd_port)

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()     
