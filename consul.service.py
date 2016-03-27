#!/usr/bin/env python
import requests
import sys

service_name = '' # update this with the service name to check

services = requests.get('http://localhost:8500/v1/health/checks/%s' % service_name).json()

critical_message = "%s failing on:" % service_name
checks = 0
failed = False

for service in services:
    if service['Status'] != 'passing':
        checks += 1
        failed = True
        critical_message += ' %s ' % service['Node']
    else:
        checks += 1

if failed:
    print critical_message + "| checks=%d;;;;" % checks
    sys.exit(2)
else:
    print "OK | checks=%d;;;;" % checks
    sys.exit(0)
