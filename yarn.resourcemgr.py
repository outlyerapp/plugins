#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['*']

excludes = ['modelertype',
            'tag.context',
            'tag.port',
            'tag.processname',
            'tag.sessionid',
            'name',
            'tag.hostname',
            'livenodemanagers',
            'tag.clustermetrics',
            'nodehttpaddress',
            'lasthealthupdate',
            'hostname',
            'healthreport',
            'state',
            'healthstatus',
            'rack',
            'nodeid']
    
metrics = {}
node_data = {}

for n in names:
    URL = 'http://%s:8088/jmx?qry=Hadoop:service=ResourceManager,name=%s' % (socket.getfqdn(), n)
    try:
        resp = requests.get(URL, timeout=60).json()['beans']
        for i in range(len(resp)):
            for k, v in resp[i].iteritems():
                if k.lower() not in excludes:
                    metrics[k] = v
                    
        # Parse info about node managers
        for i in json.loads(resp[0]['LiveNodeManagers']):
            for k, v in i.iteritems():
                node_name = i.values()[0].split('.')[0]
                if k.lower() == 'slots':
                    for a,b in v.iteritems():
                        node_data[node_name + '.' + a] = b
                elif k.lower() not in excludes:
                    node_data[node_name + '.' + k] = v
                    
        metrics.update(node_data)
    
    except:
        print "Plugin Failed!"
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output

