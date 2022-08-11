#!/usr/bin/env python

import configparser
import os
from datetime import datetime

#read config
config = configparser.ConfigParser()

def read():
    try:
        #read config
        config.read('solar-manager.ini')

        values = {}

        #read config and default values
        values["byd_ip"] = config['BydSection']['byd_ip']
        values["byd_port"] = int(config['BydSection']['byd_port'])
        if os.getenv('BYD_IP','None') != 'None':
            values["byd_ip"] = os.getenv('BYD_IP')
            print ("using env: BYD_IP")
        if os.getenv('BYD_PORT','None') != 'None':
            values["byd_port"] = int(os.getenv('BYD_PORT'))
            print ("using env: BYD_PORT")

        values["charge_start"] = int(config['ChargerSection']['charge_start'])
        values["charge_end"] = int(config['ChargerSection']['charge_end'])
        values["charge_mqtt_name"] = config['ChargerSection']['charge_mqtt_name']
        if os.getenv('CHARGE_START','None') != 'None':
            values["charge_start"] = int(os.getenv('CHARGE_START'))
            print ("using env: CHARGE_START")
        if os.getenv('CHARGE_END','None') != 'None':
            values["charge_end"] = int(os.getenv('CHARGE_END'))
            print ("using env: CHARGE_END")
        if os.getenv('CHARGE_MQTT_NAME','None') != 'None':
            values["charge_mqtt_name"] = os.getenv('CHARGE_MQTT_NAME')
            print ("using env: CHARGE_MQTT_NAME")

        values["daly1_mqtt_name"] = config['DalySection']['daly1_mqtt_name']
        values["daly2_mqtt_name"] = config['DalySection']['daly2_mqtt_name']
        values["daly3_mqtt_name"] = config['DalySection']['daly3_mqtt_name']
        if os.getenv('DALY1_MQTT_NAME','None') != 'None':
            values["daly1_mqtt_name"] = os.getenv('DALY1_MQTT_NAME')
            print ("using env: DALY1_MQTT_NAME")
        if os.getenv('DALY2_MQTT_NAME','None') != 'None':
            values["daly2_mqtt_name"] = os.getenv('DALY2_MQTT_NAME')
            print ("using env: DALY2_MQTT_NAME")
        if os.getenv('DALY3_MQTT_NAME','None') != 'None':
            values["daly3_mqtt_name"] = os.getenv('DALY3_MQTT_NAME')
            print ("using env: DALY3_MQTT_NAME")

        values["timescaledb_ip"] = config['DatabaseSection']['timescaledb_ip']
        values["timescaledb_username"] = config['DatabaseSection']['timescaledb_username']
        values["timescaledb_password"] = config['DatabaseSection']['timescaledb_password']
        if os.getenv('TIMESCALEDB_IP','None') != 'None':
            values["timescaledb_ip"] = os.getenv('TIMESCALEDB_IP')
            print ("using env: TIMESCALEDB_IP")
        if os.getenv('TIMESCALEDB_USERNAME','None') != 'None':
            values["timescaledb_username"] = os.getenv('TIMESCALEDB_USERNAME')
            print ("using env: TIMESCALEDB_USERNAME")
        if os.getenv('TIMESCALEDB_PASSWORD','None') != 'None':
            values["timescaledb_password"] = os.getenv('TIMESCALEDB_PASSWORD')
            print ("using env: TIMESCALEDB_PASSWORD")

        values["idm_ip"] = config['IdmSection']['idm_ip']
        values["idm_port"] = int(config['IdmSection']['idm_port']) 
        values["feed_in_limit"] = int(config['IdmSection']['feed_in_limit']) 
        if os.getenv('IDM_IP','None') != 'None':
            values["idm_ip"] = os.getenv('IDM_IP')
            print ("using env: IDM_IP")
        if os.getenv('IDM_PORT','None') != 'None':
            values["idm_port"] = int(os.getenv('IDM_PORT'))
            print ("using env: IDM_PORT")
        if os.getenv('FEED_IN_LIMIT','None') != 'None':
            values["feed_in_limit"] = int(os.getenv('FEED_IN_LIMIT'))
            print ("using env: FEED_IN_LIMIT")

        values["inverter_ip"] = config['KostalSection']['inverter_ip']
        values["inverter_port"] = int(config['KostalSection']['inverter_port'])
        if os.getenv('INVERTER_IP','None') != 'None':
            values["inverter_ip"] = os.getenv('INVERTER_IP')
            print ("using env: INVERTER_IP")
        if os.getenv('INVERTER_PORT','None') != 'None':
            values["inverter_port"] = int(os.getenv('INVERTER_PORT'))
            print ("using env: INVERTER_PORT")

        values["mqtt_broker"] = config['MqttSection']['mqtt_broker']
        values["mqtt_port"] = int(config['MqttSection']['mqtt_port'])
        values["mqtt_user"] = config['MqttSection']['mqtt_user']
        values["mqtt_password"] = config['MqttSection']['mqtt_password']
        if os.getenv('MQTT_BROKER','None') != 'None':
            values["mqtt_broker"] = os.getenv('MQTT_BROKER')
            print ("using env: MQTT_BROKER")
        if os.getenv('MQTT_PORT','None') != 'None':
            values["mqtt_port"] = int(os.getenv('MQTT_PORT'))
            print ("using env: MQTT_PORT")
        if os.getenv('MQTT_USER','None') != 'None':
            values["mqtt_user"] = os.getenv('MQTT_USER')
            print ("using env: MQTT_USER")
        if os.getenv('MQTT_PASSWORD','None') != 'None':
            values["mqtt_password"] = os.getenv('MQTT_PASSWORD')
            print ("using env: MQTT_PASSWORD")

        values["rs485_device"] = config['RS485Section']['rs485_device']  
        values["numberOfUnits"] = int(config['RS485Section']['numberOfUnits'] )
        values["maxOutput"] = int(config['RS485Section']['maxOutput'])
        if os.getenv('RS485_DEVICE','None') != 'None':
            values["rs485_device"] = os.getenv('RS485_DEVICE')
            print ("using env: RS485_DEVICE")
        if os.getenv('NUMBEROFUNITS','None') != 'None':
            values["numberOfUnits"] = int(os.getenv('NUMBEROFUNITS'))
            print ("using env: NUMBEROFUNITS")
        if os.getenv('MAXOUTPUT','None') != 'None':
            values["maxOutput"] = int(os.getenv('MAXOUTPUT'))
            print ("using env: MAXOUTPUT")

        values["server_mqtt_name"] = config['ServerSection']['server_mqtt_name']
        if os.getenv('SERVER_MQTT_NAME','None') != 'None':
            values["server_mqtt_name"] = os.getenv('SERVER_MQTT_NAME')
            print ("using env: SERVER_MQTT_NAME")
        
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " config: ", values)

        return values
    except Exception as ex:
        print ("ERROR Config: ", ex) 
