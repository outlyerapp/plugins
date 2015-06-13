#!/usr/bin/env python
import wmi
import sys

"""
Show current running services on Windows by running : net start
Enter the ones you want to alert on into checks
"""

checks = ['']
service_map = {}

c = wmi.WMI()
services = c.Win32_Service()
for s in services :
    service_map[s.Caption] = s.State

output = ""
exit = 0
for check in checks:
    if service_map[check] == "Running":
        output += check + " is running! "
    else:
        output += check + " is down! "
        exit = 2

print output
sys.exit(exit)
