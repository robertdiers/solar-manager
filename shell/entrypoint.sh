printenv | grep -v "no_proxy" >> /etc/environment
echo 'environment stored - waiting for timescaledb'
sleep 60
cd /app
python3 python/init.py
echo 'database initialized - starting cron'
cron -f