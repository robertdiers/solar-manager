# solar-manager

## Setup:
* Kostal inverter with BYD storage
* Kostal energy meter
* iDM Heat Pump AERO SLM 6-17 with "solar input" feature
* additional 48V battery block
* Tasmota device to manage a 48V charger (Sonoff POWR3)
* 3 SoyoSource GTN 1200 (Grid Tie inverter)
* USB to RS485 dongle to manage the SoyoSource output
* Orange Pi 3 LTS to run the containers and USB dongle
* Tasmota device to manage Orange Pi power including temperature sensor (Sonoff TH16 + Si7021)

## main Python scripts (startup and cron triggered):
* init.py - initializes TimescaleDB tables as they are removed when device restarts
* daly-subscribe.py - subscribes to DALY MQTT output and store to database (https://github.com/softwarecrash/DALY-BMS-to-MQTT)
* metrics.py - collect metrics and store to database
* rs485.py - sends "to produce" value to Soyosource inverters using RS485 USB dongle
* solar-manager.py - business logic

## additional Python modules
* BYD.py - read actual values from BYD battery (TCP Socket)
* Config.py - read config file and check for environment parameter overrides
* Daly.py - subscribes to MQTT topic to read JSON with data
* IdmPump.py - send actual solar power to iDM heat pump (TCP Modbus)
* Kostal.py - read actual values from Kostal inverter (TCP Modbus)
* Tasmota.py - turn Tasmota device on/off and read status (MQTT)
* TimescaleDb.py - read and write TimescaleDB

## Docker
```
docker run -d --restart always --device=/dev/ttyUSB0:/dev/ttyUSB0 --name solarmanager robertdiers/solarmanager:arm64
```

### TimescaleDB
Using /dev/shm to store data in memory, sd card doesn't have to store it:

```
docker run -d --restart always --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password -v /dev/shm/pgdata:/var/lib/postgresql/data timescale/timescaledb:latest-pg14
```

### Grafana
Dashboard JSON is placed in this repo:

```
docker run -d --name grafana --volume "$PWD/grafanadata:/var/lib/grafana" -p 3000:3000 --restart always grafana/grafana:latest
```

### EMQX (MQTT broker)
```
docker run -d --name emqx -p 18083:18083 -p 1883:1883 -v $PWD/emqxdata:/opt/emqx/data --restart always emqx:latest
```

