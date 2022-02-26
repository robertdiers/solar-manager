FROM codercom/code-server:3.11.1

USER root

#install environment requirements
RUN apt update
RUN apt -y upgrade
RUN apt -y install gcc
RUN apt -y install cron python3 python3-pip libpq-dev python3-dev
RUN pip3 install configparser pymodbus psycopg2

#install code extensions
#RUN code-server --install-extension ms-python.python
