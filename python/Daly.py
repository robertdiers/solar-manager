#!/usr/bin/env python

import time
import json
from paho.mqtt import client as mqtt_client

internaltopic = "unknown"
internalcallback = "unknown"
internalname = "unknown"

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
    content = str(message.payload.decode("utf-8"))
    #print(content)
    json_object = flatten_json(json.loads(content))
    #print(json_object)
    global internalcallback
    global internalname
    internalcallback(internalname, json_object)

def subscribe(mqtt_broker, mqtt_port, mqtt_user, mqtt_password, topic, callback, name):
    try:
        
        client_id = 'solarmanager-'+name

        # Set Connecting Client ID
        client = mqtt_client.Client(client_id)
        client.username_pw_set(mqtt_user, mqtt_password)
        client.connect(mqtt_broker, mqtt_port)

        global internaltopic
        internaltopic = topic
        global internalcallback
        internalcallback = callback
        global internalname
        internalname = name

        client.on_message=on_message
        client.subscribe(internaltopic)
        client.loop_start()

        return client 
    except Exception as ex:
        print ("ERROR Daly: ", ex)    

def close(client):
    client.loop_stop()
    global internaltopic
    client.unsubscribe(internaltopic)
