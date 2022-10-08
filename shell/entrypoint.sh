printenv | grep -v "no_proxy" >> /etc/environment
echo 'environment stored - waiting for timescaledb'
sleep 60
cd /app/python
echo 'starting database init'
python3 init.py
echo 'starting cron'
cd /app
cron -f