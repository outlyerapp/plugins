#!/usr/bin/env python
import sys
import requests
import json
import socket

excludes = ['name', 'modelertype']
    
metrics = {}
node_data = {}

URL = 'http://%s:9095/jmx?qry=hadoop:service=thrift,name=Thrift' % socket.getfqdn()
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

