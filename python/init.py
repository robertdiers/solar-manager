#!/usr/bin/env python

import Config
import TimescaleDb

if __name__ == "__main__":  
    try:
        conf = Config.read()

        TimescaleDb.connect(conf["timescaledb_ip"], conf["timescaledb_username"], conf["timescaledb_password"])

        # execute init script
        file1 = open('init.sql', 'r')
        Lines = file1.readlines()
        
        # Strips the newline character
        for line in Lines:
            TimescaleDb.exec(line)
            print("SQL: {}".format(line))
        
    except Exception as ex:
        print ("ERROR: ", ex) 
    finally:
        TimescaleDb.close()      
