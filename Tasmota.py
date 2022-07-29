#!/usr/bin/env python

import configparser
import os
from datetime import datetime
from paho.mqtt import client as mqtt_client

#read config
config = configparser.ConfigParser()

def on(client, name):
    topic = "cmnd/" + name + "/Power"
    #print(topic)
    client.publish(topic, "ON")

def off(client, name):
    topic = "cmnd/" + name + "/Power"
    #print(topic)
    client.publish(topic, "OFF")

def connect():
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        tasmota_mqtt_broker = config['ChargerSection']['tasmota_mqtt_broker']
        tasmota_mqtt_port = config['ChargerSection']['tasmota_mqtt_port']
        tasmota_mqtt_user = config['ChargerSection']['tasmota_mqtt_user']
        tasmota_mqtt_password = config['ChargerSection']['tasmota_mqtt_password']

        # override with environment variables
        if os.getenv('TASMOTA_MQTT_BROKER','None') != 'None':
            tasmota_mqtt_broker = os.getenv('TASMOTA_MQTT_BROKER')
            print ("using env: TASMOTA_MQTT_BROKER")
        if os.getenv('TASMOTA_MQTT_PORT','None') != 'None':
            tasmota_mqtt_port = os.getenv('TASMOTA_MQTT_PORT')
            print ("using env: TASMOTA_MQTT_PORT")
        if os.getenv('TASMOTA_MQTT_USER','None') != 'None':
            tasmota_mqtt_user = os.getenv('TASMOTA_MQTT_USER')
            print ("using env: TASMOTA_MQTT_USER")
        if os.getenv('TASMOTA_MQTT_PASSWORD','None') != 'None':
            tasmota_mqtt_password = os.getenv('TASMOTA_MQTT_PASSWORD')
            print ("using env: TASMOTA_MQTT_PASSWORD")

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_mqtt_broker: ", tasmota_mqtt_broker)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_mqtt_port: ", tasmota_mqtt_port)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_mqtt_user: ", tasmota_mqtt_user)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " tasmota_mqtt_password: ", tasmota_mqtt_password)
        
        client_id = 'python-mqtt-solarmanager'

        # Set Connecting Client ID
        client = mqtt_client.Client(client_id)
        client.username_pw_set(tasmota_mqtt_user, tasmota_mqtt_password)
        client.connect(tasmota_mqtt_broker, int(tasmota_mqtt_port))

        return client  
    except Exception as ex:
        print ("ERROR: ", ex)    
