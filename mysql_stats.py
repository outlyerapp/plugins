#!/usr/bin/env python
import subprocess
import re
import sys

"""
You may need to update the MYSQL_USER and MYSQL_PASSWORD with an account that can connect.
"""

MYSQL_USER = ''
MYSQL_PASSWORD = ''

command = ['/usr/bin/mysql', '-s', '-N', '-s', '-e', 'show global status']
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
metric_list = status.split('\n')
for line in metric_list:
    if line:
        metric = line.split('\t')
        k = metric[0].strip().lower()
        v = metric[1]
        output += k + '=' + v + ';;;; '

print output
sys.exit(0)

