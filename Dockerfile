FROM debian:stable-slim

RUN apt update
RUN apt -y upgrade
RUN apt -y install gcc
RUN apt -y install cron python3 python3-pip libpq-dev python3-dev
RUN pip3 install configparser pymodbus psycopg2

# copy files
COPY init.sql /app/init.sql
COPY init.py /app/init.py
COPY rs485.py /app/rs485.py
COPY rs485.ini /app/rs485.ini
COPY rs485.sh /app/rs485.sh
COPY solar-manager.py /app/solar-manager.py
COPY solar-manager.ini /app/solar-manager.ini
COPY solar-manager.sh /app/solar-manager.sh
COPY entrypoint.sh /app/entrypoint.sh
COPY container_cron /etc/cron.d/container_cron

# set workdir
WORKDIR /app

# give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/container_cron

# apply cron job
RUN crontab /etc/cron.d/container_cron

# run the command on container startup
CMD ["bash", "entrypoint.sh"]
