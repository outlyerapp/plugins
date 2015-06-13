#!/usr/bin/env python
import sys
import requests
import json
import socket

names = ['*']

excludes = ['']
    
metrics = {}
for n in names:
    URL = 'http://%s:50060/jmx?qry=hadoop:service=TaskTracker,name=%s' % (socket.getfqdn(), n)
    try:
        resp = requests.get(URL, timeout=60).json()['beans'][0]['TasksInfoJson']
        task_info = json.loads(resp)
        for k, v in task_info.iteritems():
           metrics[k] = v

    except Exception, e:
        print "Plugin Failed!"
        sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k).lower() + '=' + str(v).lower() + ';;;; '

print output

