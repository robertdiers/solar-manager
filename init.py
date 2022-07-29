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
        
        #init Timescaledb
        conn = TimescaleDb.connect()

        # execute init script
        # Using readlines()
        file1 = open('init.sql', 'r')
        Lines = file1.readlines()
        
        # Strips the newline character
        for line in Lines:
            TimescaleDb.exec(conn, line)
            print("SQL: {}".format(line))

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " INIT END #####")
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        if conn is not None:
            TimescaleDb.close(conn)
            #print('Database connection closed.')          
