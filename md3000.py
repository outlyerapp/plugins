#!/usr/bin/env python
import sys
import os
import subprocess

# settings
controller = '192.168.0.1'

def smcli(p):
    try:
        return subprocess.check_output(['sudo', 'SMcli', controller, '-S', '-c', p])
    except Exception, e:
        print "Plugin Failed: %s" % e
        sys.exit(2)

success_message = "OK - "
fail_message = "FAIL! - "
critical = False

health_output = smcli('show storageArray healthStatus;')

if health_output.strip() == 'Storage array health status = optimal.':
    success_message += "Array is Healthy. "
else:
    fail_message += "Array is Critical. "
    critical = True

virtualdisk_output = smcli('show allvirtualdisks summary;')
table = virtualdisk_output.split('\n')[5:]
for line in table:
    if 'Optimal' not in line and len(line) > 0:
        fail_message += line.split(' ')[0] + ' is not optimal. '
        critical = True
success_message += "Virtual disks healthy. "
    
unreadable_output = smcli('show storageArray unreadablesectors;')
if unreadable_output.strip() == 'There are currently no unreadable sectors on the storage array.':
    success_message += "No unreadable sectors. "
else:
    fail_message += "Array has unreadable sectors! "
    critical = True

if critical:
    print fail_message
    sys.exit(2)
else:
    print success_message
    sys.exit(0)
