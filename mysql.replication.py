#!/usr/bin/env python
"""
Update the MYSQL_USER and MYSQL_PASSWORD variables below.
"""
import subprocess
import re
import sys

MYSQL_USER = ''
MYSQL_PASSWORD = ''


command = ['/usr/bin/mysql', '-t', '-E', '-N', '-s', '--column-names', '-e', "show slave status"]

if MYSQL_USER:
    command.append('-u%s' % MYSQL_USER)
if MYSQL_PASSWORD:
    command.append('-p%s' % MYSQL_PASSWORD)

try:
    slave_status = subprocess.check_output(command)
except:
    print "Plugin Failed!"
    sys.exit(2)

output = "OK | "

slave_metric_list = slave_status.split('\n')

repl_status=0
stats_count=0

for line in slave_metric_list:
    if line and ':' in line:
        stats_count = 1
        metric = line.split(':')
        k = metric[0].strip().lower()
        v = metric[1].strip()
        output += k + '=' + v + ';;;; '
        if k in ('slave_io_running','slave_sql_running'):
            if v == 'No':
                print '%s appears to be false!' %k
                repl_status += 1

if stats_count < 1:
    print "This server does not appear to be a replication slave!"
    sys.exit(1)
        
print output
sys.exit(repl_status)
