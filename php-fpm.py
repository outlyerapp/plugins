#!/usr/bin/env python

import sys
import requests

""" This script requires some configuration.

1. edit /etc/php5/fpm/pool.d/www.conf and uncomment pm.status_path to enable it

2. add the following block to nginx

location ~ ^/(www-status)$ {
     access_log off;
     allow 127.0.0.1;
     deny all;
     include fastcgi_params;
     fastcgi_pass 127.0.0.1:9000;
}

3. restart nginx and php-fpm
"""

HOST = 'localhost'
PORT = 80
URL = "http://%s:%s/www-status" % (HOST, PORT)

excludes = ['pool', 'process_manager', 'start_time']

try:
    resp = requests.get(URL).content.split('\n')
except:
    print "connection failed"
    sys.exit(2)

result = "OK | "

for metric in resp:
    if len(metric) > 0:
        key = metric.split(':')[0].replace(' ', '_').lower().strip()
        if not any(x in key.lower() for x in excludes):
            value = metric.split(':')[1].strip()
            result += key + "=" + str(value) + ";;;; "

print result
sys.exit(0)

