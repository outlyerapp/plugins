#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['*']

excludes = ['tag.context',
            'modelertype',
            'tag.port',
            'tag.processname',
            'tag.sessionid',
            'name',
            'tag.hostname']
    
metrics = {}
node_data = {}

for n in names:
    URL = 'http://%s:8042/jmx?qry=Hadoop:service=NodeManager,name=%s' % (socket.getfqdn(), n)
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

