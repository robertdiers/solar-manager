#!/usr/bin/env python

import os
import psycopg2
import math

conn = "unknown"

# write metric to TimescaleDB
def write(table, value):
    global conn  
    # create a cursor      
    cur = conn.cursor()   
    # execute a statement
    sql = 'insert into metrics (time, key, value) values (now(), %s, %s)'
    cur.execute(sql, (table,value,))   
    # commit the changes to the database
    conn.commit()
    # close the communication with the PostgreSQL
    cur.close()

# read from TimescaleDB
def read(table):
    global conn
    # create a cursor   
    cur = conn.cursor()   
    # execute a statement
    sql = 'SELECT value FROM '+table
    cur.execute(sql)  
    row = cur.fetchone()
    value = row[0]
    if math.isnan(value):
        value = 0
    # close the communication with the PostgreSQL
    cur.close()
    return value

# increase value in TimescaleDB
def increase(table, value, maxValue):
    # create a cursor
    global conn
    cur = conn.cursor()
    valueold = read(table)
    # calculation
    valuenew = valueold + value
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
def exec(sql):
    try:
        global conn
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

def connect(timescaledb_ip, timescaledb_username, timescaledb_password):
    try:       
        
        #init Timescaledb
        global conn
        conn = psycopg2.connect(
            host=timescaledb_ip,
            database="postgres",
            user=timescaledb_username,
            password=timescaledb_password)
        
    except Exception as ex:
        print ("ERROR: ", ex)         

def close():
    global conn
    conn.close()
