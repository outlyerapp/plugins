#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['R*', 'N*', 'F*', 'U*']

excludes = ['name',
            'tag.Hostname',
            'modelerType',
            'tag.Context',
            'tag.port',
            'LiveNodes',
            'NameDirStatuses']

metrics = {}
for n in names:
    URL = 'http://%s:50070/jmx?qry=Hadoop:service=NameNode,name=%s' % (socket.getfqdn(), n)
    try:
        resp = requests.get(URL, timeout=60).json()['beans']
        for i in range(len(resp)):
            for k, v in resp[i].iteritems():
                if k not in excludes:
                    metrics[k] = v
    
    except Exception, e:
        print "Plugin Failed!"
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output
sys.exit(0)
