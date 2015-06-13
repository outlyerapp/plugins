#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['*']

excludes = ['name',
            'modelertype']
    
metrics = {}
node_data = {}

for n in names:
    URL = 'http://%s:8085/jmx?qry=hadoop:service=rest,name=%s' % (socket.getfqdn(), n)
    try:
        resp = requests.get(URL, timeout=60).json()['beans']
        for i in range(len(resp)):
            for k, v in resp[i].iteritems():
                if k.lower() not in excludes:
                    metrics[k] = v
    except:
        print "Plugin Failed!"
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output

