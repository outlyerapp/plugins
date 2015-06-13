#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['*']

excludes = ['blacklistednodesinfojson',
            'configversion',
            'name',
            'hostname',
            'modelertype',
            'version',
            'queueinfojson',
            'alivenodesinfojson',
            'hostname',
            'health',
            'last_seen',
            'slots',
            'summaryjson']
    
metrics = {}
node_data = {}
sum_data = {}
for n in names:
    URL = 'http://%s:50030/jmx?qry=hadoop:service=JobTracker,name=%s' % (socket.getfqdn(), n)
    try:
        resp = requests.get(URL, timeout=60).json()['beans']
        
        # Get all of the top level metrics
        for i in range(len(resp)):
            for k, v in resp[i].iteritems():
                if k.lower() not in excludes:
                    metrics[k] = v
        
        # Parse info about individual nodes
        for i in json.loads(resp[0]['AliveNodesInfoJson']):
            for k, v in i.iteritems():
                node_name = i.values()[0].split('.')[0]
                if k.lower() == 'slots':
                    for a,b in v.iteritems():
                        node_data[node_name + '.' + a] = b
                elif k.lower() not in excludes:
                    node_data[node_name + '.' + k] = v
        metrics.update(node_data)
        
        # Parse summary data
        summary = json.loads(resp[0]['SummaryJson'])
        for k, v in summary.iteritems():
            if k.lower() == 'slots':
                for a,b in v.iteritems():
                    sum_data['total_' + a] = b
            elif k.lower() not in excludes:       
                sum_data['total_' + k] = v
        
        metrics.update(sum_data)
   
    except:
        print "Plugin Failed!"
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output

