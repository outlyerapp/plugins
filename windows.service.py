#!/usr/bin/env python
import sys
import subprocess

# set to the name of the service as shown by 'sc query' i.e not the display name
SERVICE = ''

try:
    service_info = subprocess.check_output(['sc', 'query', SERVICE])
    service = {}
    for line in service_info.splitlines():
        fields = line.split(':')
        if len(fields) > 1:
            k = fields[0].strip().lower()
            v = fields[1].strip().lower()
            service[k] = v
    if 'running' in service['state']:
        print "OK"
        sys.exit(0)
    else:
        print "Service is NOT running"
        sys.exit(2)
        
except Exception, e:
    print "Plugin Failed: %s" % e
    sys.exit(2)
