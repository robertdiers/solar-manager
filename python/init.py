#!/usr/bin/env python

import configparser
import os
import serial
from datetime import datetime

import TimescaleDb

#read config
config = configparser.ConfigParser()

if __name__ == "__main__":  
    print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " INIT START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        timescaledb_ip = config['DatabaseSection']['timescaledb_ip']
        timescaledb_username = config['DatabaseSection']['timescaledb_username']
        timescaledb_password = config['DatabaseSection']['timescaledb_password']

        if os.getenv('TIMESCALEDB_IP','None') != 'None':
            timescaledb_ip = os.getenv('TIMESCALEDB_IP')
            print ("using env: TIMESCALEDB_IP")
        if os.getenv('TIMESCALEDB_USERNAME','None') != 'None':
            timescaledb_username = os.getenv('TIMESCALEDB_USERNAME')
            print ("using env: TIMESCALEDB_USERNAME")
        if os.getenv('TIMESCALEDB_PASSWORD','None') != 'None':
            timescaledb_password = os.getenv('TIMESCALEDB_PASSWORD')
            print ("using env: TIMESCALEDB_PASSWORD")
        
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_ip: ", timescaledb_ip)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_username: ", timescaledb_username)
        #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " timescaledb_password: ", timescaledb_password)

        TimescaleDb.connect(timescaledb_ip, timescaledb_username, timescaledb_password)

        # execute init script
        # Using readlines()
        #file1 = open('adhoc.sql', 'r')
        file1 = open('init.sql', 'r')
        Lines = file1.readlines()
        
        # Strips the newline character
        for line in Lines:
            TimescaleDb.exec(line)
            print("SQL: {}".format(line))

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " INIT END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()      
