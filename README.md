# solar-manager

3 main Python scripts (startup and cron triggered):
* init.py - initializes TimescaleDB tables as they are removed when device restarts
* solar-manager.py - business logic
* rs485.py - sends "to produce" value to Soyosource inverters using RS485 USB dongle

## Python modules
* BYD.py - read actual values from BYD battery (TCP Socket)
* IdmPump.py - send actual solar power to iDM heat pump (TCP Modbus)
* Kostal.py - read actual values from Kostal inverter (TCP Modbus)
* Tasmota.py - turn Tasmota device on/off and read status (MQTT)
* TimescaleDb.py - read and write TimescaleDB

## Docker
docker run -d --restart always --device=/dev/ttyUSB0:/dev/ttyUSB0 --name solarmanager robertdiers/solarmanager:arm64

## TimescaleDB
Using /dev/shm to store data in memory, sd card doesn't have to store it:

docker run -d --restart always --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password -v /dev/shm/pgdata:/var/lib/postgresql/data timescale/timescaledb:latest-pg14
