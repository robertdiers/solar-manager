FROM docker.io/debian:stable-slim

RUN apt update
RUN apt -y upgrade
RUN apt -y install gcc
RUN apt -y install cron python3 python3-pip libpq-dev python3-dev
RUN pip3 install configparser pymodbus psycopg2 paho-mqtt

# copy files
COPY python /app/python
COPY shell/rs485.sh /app/rs485.sh
COPY shell/solar-manager.sh /app/solar-manager.sh
COPY shell/entrypoint.sh /app/entrypoint.sh
COPY shell/container_cron /etc/cron.d/container_cron

# set workdir
WORKDIR /app

# give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/container_cron

# apply cron job
RUN crontab /etc/cron.d/container_cron

# run the command on container startup
CMD ["bash", "entrypoint.sh"]
