#!/usr/bin/env python

import configparser
import os
import psycopg2
import math
from datetime import datetime

#read config
config = configparser.ConfigParser()

# write metric to TimescaleDB
def write(conn, table, value):
    # create a cursor
    cur = conn.cursor()   
    # execute a statement
    sql = 'insert into '+table+' (time, value) values (now(), %s)'
    cur.execute(sql, (value,))   
    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()

# read metric to TimescaleDB
def read(conn, table):
    # create a cursor
    cur = conn.cursor()   
    # execute a statement
    sql = 'SELECT value FROM '+table
    cur.execute(sql)  
    row = cur.fetchone()
    value = row[0]
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " value: " + str(value)) 
    if math.isnan(value):
        value = 0
    # close the communication with the PostgreSQL
    cur.close()
    return value

# increase value in TimescaleDB
def increase(conn, table, value, maxValue):
    # create a cursor
    cur = conn.cursor()
    valueold = read(conn, table)
    # calculation
    valuenew = valueold + value
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " valuenew: " + str(valuenew)) 
    # max/min check 
    if maxValue < valuenew:
        valuenew = maxValue
    if 0 > valuenew:
        valuenew = 0
    # execute a statement
    sql = 'update '+table+' set value = %s'
    cur.execute(sql, (valuenew,))
    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()
    return valuenew

# exec in db
def exec(conn, sql):
    try:
        # create a cursor
        cur = conn.cursor()   
        # execute a statement
        cur.execute(sql)  
        # commit the changes to the database
        conn.commit()
        # close the communication with the PostgreSQL
        cur.close()
    except Exception as ex:
        print ("ERROR: ", ex) 

def connect():  
    #print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " START #####")
    try:
        #read config
        config.read('solar-manager.ini')

        #read config and default values
        timescaledb_ip = config['MetricSection']['timescaledb_ip']
        timescaledb_username = config['MetricSection']['timescaledb_username']
        timescaledb_password = config['MetricSection']['timescaledb_password']

        # override with environment variables
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
        
        #init Timescaledb
        conn = psycopg2.connect(
            host=timescaledb_ip,
            database="postgres",
            user=timescaledb_username,
            password=timescaledb_password)        

        return conn
        
    except Exception as ex:
        print ("ERROR: ", ex)         

def close(conn):
    if conn is not None:
        conn.close()
