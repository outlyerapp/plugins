#!/usr/bin/env python
"""
Update the MYSQL_USER and MYSQL_PASSWORD variables below.
"""
import subprocess
import re
import sys

"""
This script runs /usr/bin/mysqladmin status and cuts up the output into Nagios format.
You may need to update the MYSQL_USER and MYSQL_PASSWORD with an account that can connect. 
"""

MYSQL_USER = 'root'
MYSQL_PASSWORD = ''

command = ['/usr/bin/mysqladmin', 'status']
if MYSQL_USER:
    command.append('-u%s' % MYSQL_USER)
if MYSQL_PASSWORD:
    command.append('-p%s' % MYSQL_PASSWORD)

try:
    status = subprocess.check_output(command)
except:
    print "connection failure"
    sys.exit(2)

output = "OK | "
metric_list = status.split('  ')
for metric in metric_list:
    k = metric.split(':')[0].lower().replace(' ', '_').strip()
    v = metric.split(':')[1].strip()
    output += k + '=' + v + ';;;; '

print output
sys.exit(0)

