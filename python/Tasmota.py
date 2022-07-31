#!/usr/bin/env python

import configparser
import os
import time
import json
from datetime import datetime
from paho.mqtt import client as mqtt_client

#read config
config = configparser.ConfigParser()
client = "unknown"
searchattribute = "unknown"
valueattribute = "unknown"

def on(name):
    topic = "cmnd/" + name + "/Power"
    #print(topic)
    global client
    client.publish(topic, "ON")

def off(name):
    topic = "cmnd/" + name + "/Power"
    #print(topic)
    global client
    client.publish(topic, "OFF")

def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

def on_message(client, userdata, message):
    global searchattribute
    global valueattribute
    content = str(message.payload.decode("utf-8"))
    #print(content)
    json_object = flatten_json(json.loads(content))
    #print(json_object)
    if searchattribute in json_object:
        valueattribute = json_object[searchattribute]
    else:
        valueattribute = "n/a"

def get(name, statusnumber, attribute):
    topic = "cmnd/" + name + "/Status"
    topicstat = "stat/" + name + "/#"
    #print(topic)
    global client
    global searchattribute
    global valueattribute
    searchattribute = attribute
    valueattribute = "unknown"
    client.on_message=on_message
    client.subscribe(topicstat)
    client.loop_start()
    #send status request to tasmota
    client.publish(topic, statusnumber)
    counter = 0
    #wait max 5 sec
    while valueattribute in ["unknown"] and counter < 50:
        counter = counter + 1
        time.sleep(0.1)
    client.loop_stop()
    #print(valueattribute)
    return valueattribute

def connect():
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        mqtt_broker = config['MqttSection']['mqtt_broker']
        mqtt_port = config['MqttSection']['mqtt_port']
        mqtt_user = config['MqttSection']['mqtt_user']
        mqtt_password = config['MqttSection']['mqtt_password']

        # override with environment variables
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

        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_broker: ", mqtt_broker)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_port: ", mqtt_port)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_user: ", mqtt_user)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " mqtt_password: ", mqtt_password)
        
        client_id = 'python-mqtt-solarmanager'

        # Set Connecting Client ID
        global client
        client = mqtt_client.Client(client_id)
        client.username_pw_set(mqtt_user, mqtt_password)
        client.connect(mqtt_broker, int(mqtt_port))
 
    except Exception as ex:
        print ("ERROR: ", ex)    
