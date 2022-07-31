printenv | grep -v "no_proxy" >> /etc/environment
echo 'environment stored - waiting for timescaledb'
sleep 60
cd /app/python
python3 init.py
echo 'database initialized - starting cron'
cd /app
cron -f