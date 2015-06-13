#!/usr/bin/env python
"""
Update the MYSQL_USER and MYSQL_PASSWORD variables below.
"""
import os
import re
import subprocess
import sys
import time
import json
from datetime import datetime

MYSQL_USER = ''
MYSQL_PASSWORD = ''

TIMESTAMP = datetime.now().strftime('%s')
status = {}


def get_mysql_active_connections():
    active_connections = ['/usr/bin/mysql', '-N', '-A', '-s', '-e', "select  user, case count(*) when 1 then 0 else count(*) -1 end \
                    from (select user from information_schema.processlist where state is not null and state !='' union all select distinct user from mysql.user) as users group by user;"]
    if MYSQL_USER:
        active_connections.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        active_connections.append('-p%s' % MYSQL_PASSWORD)

    try:
        resp = subprocess.check_output(active_connections)
    except:
        print "Plugin Failed!"
        sys.exit(2)
        
    metric_list = resp.split('\n')
    metric_list.sort()
    for line in metric_list:
        if line:
            metric = line.split('\t')
            k =  metric[0].strip().lower()
            k = k.replace(' ', '_',1)
            v = metric[1]
            status[k] = v
    return status


def get_mysql_all_connections():
    all_connections = ['/usr/bin/mysql', '-N', '-A', '-s', '-e', "select  user, case count(*) when 1 then 0 else count(*) -1 end \
                    from (select user from information_schema.processlist union all select distinct user from mysql.user) as users group by user;"]
    if MYSQL_USER:
        all_connections.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        all_connections.append('-p%s' % MYSQL_PASSWORD)
    
    try:
        resp = subprocess.check_output(all_connections)
    except:
        print "Plugin Failed!"
        sys.exit(2)
    
    metric_list = resp.split('\n')
    metric_list.sort()
    for line in metric_list:
        if line:
            metric = line.split('\t')
            k =  metric[0].strip().lower()
            k = k.replace(' ', '_',1)
            v = metric[1]
            status[k] = v
    return status

### Main program

# get the current status
active_result = get_mysql_active_connections()
all_result = get_mysql_all_connections()

# Finally nagios exit with perfdata
connection_data = "OK | "
for k, v in active_result.iteritems():
    connection_data += "%s_active=%s;;;; " % (k, v)
for k, v in all_result.iteritems():
    connection_data += "%s_total=%s;;;; " % (k, v)
print connection_data
sys.exit(0)
