printenv | grep -v "no_proxy" >> /etc/environment
echo 'environment stored - starting cron'
cron -f