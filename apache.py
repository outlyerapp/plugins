#!/usr/bin/env python
import sys
import requests
import re

"""
This plugin expects the apache status page to be available on /server-status?auto
To enable simply add this block to your httpd.conf:

  <Location /server-status>
  SetHandler server-status
  </Location>

For more info including how to make that more secure visit http://httpd.apache.org/docs/2.2/mod/mod_status.html
"""

HOST = 'localhost'
PORT = 80
URL = "http://%s:%s/server-status?auto" % (HOST, PORT)

excludes = ['scoreboard', 'uptime']

try:
    resp = requests.get(URL).content.split('\n')
    print resp
except:
    print "connection failed"
    sys.exit(2)

result = "OK | "

for metric in resp:
    if len(metric) > 0:
        key = metric.split(':')[0].replace(' ', '.').lower().strip()
        if not any(x in key for x in excludes):
            value = float(metric.split(':')[1].strip())
            result += key + "=" + str(value) + ";;;; "

print result
sys.exit(0)

