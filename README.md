# solar-manager

combine Kostal, iDM, Soyosource and charger management


docker run -d --restart always --device=/dev/ttyUSB0:/dev/ttyUSB0 --name solarmanager robertdiers/solarmanager:arm64


## TimescaleDB

Using /dev/shm to store data in memory, sd card doesn't have to store it:

docker run -d --restart always --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password -v /dev/shm/pgdata:/var/lib/postgresql/data timescale/timescaledb:latest-pg14
