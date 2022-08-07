#!/usr/bin/env python

import os
import time
import json
from datetime import datetime
from paho.mqtt import client as mqtt_client

client = "unknown"
searchattributes = []
valueattributes = []

def on(name):
    try:
        topic = "cmnd/" + name + "/Power"
        #print(topic)
        global client
        client.publish(topic, "ON")
    except Exception as ex:
        print ("ERROR Tasmota: ", ex) 

def off(name):
    try:
        topic = "cmnd/" + name + "/Power"
        #print(topic)
        global client
        client.publish(topic, "OFF")
    except Exception as ex:
        print ("ERROR Tasmota: ", ex) 

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
    global searchattributes
    global valueattributes
    content = str(message.payload.decode("utf-8"))
    #print(content)
    json_object = flatten_json(json.loads(content))
    #print(json_object)
    for attribute in searchattributes:
        if attribute in json_object:
            valueattributes.append(json_object[attribute])
        else:
            valueattributes.append("n/a")

def get(name, statusnumber, attributes):
    try:
        topic = "cmnd/" + name + "/Status"
        topicstat = "stat/" + name + "/#"
        #print(topic)
        global client
        global searchattributes
        global valueattributes
        searchattributes = attributes
        valueattributes = []
        client.on_message=on_message
        client.subscribe(topicstat)
        client.loop_start()
        #send status request to tasmota
        client.publish(topic, statusnumber)
        counter = 0
        #wait max 5 sec
        while len(valueattributes) == 0 and counter < 50:
            counter = counter + 1
            time.sleep(0.1)
        client.loop_stop()
        #print(valueattributes)
        return valueattributes
    except Exception as ex:
        print ("ERROR Tasmota: ", ex) 

def connect(mqtt_broker, mqtt_port, mqtt_user, mqtt_password):
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        
        client_id = 'python-mqtt-solarmanager'

        # Set Connecting Client ID
        global client
        client = mqtt_client.Client(client_id)
        client.username_pw_set(mqtt_user, mqtt_password)
        client.connect(mqtt_broker, int(mqtt_port))
 
    except Exception as ex:
        print ("ERROR Tasmota: ", ex)    
