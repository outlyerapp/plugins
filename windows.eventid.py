#!/usr/bin/env python

import sys
import subprocess
import xml.etree.ElementTree as ET

#############################################################################
# This plugin searches the Windows Event Log for events matching a given    #
# Event ID within the last 60 seconds. It reports the count of events as    #
# a metric, and will exit with CRITICAL status if the count is greater      #
# than zero.                                                                #
#                                                                           #
# Tested on Windows Server 2012R2, but should run on any version of         #
# Windows where wevtutil.exe is present.                                    #
#############################################################################

# Name of the Event Log to search. Usually this would be "System"
# or "Application".
LOG_NAME = 'System'

# Event ID to search for.
EVENT_ID = 7000

# Time window to search. You should set the plugin execution frequency
# to the same value. It is recommended to leave both values at 60 seconds.
TIME_WINDOW = 60 # in seconds


query = "Event[{}[(EventID={}) and TimeCreated[timediff(@SystemTime) <= {}]]]".format(LOG_NAME, EVENT_ID, TIME_WINDOW * 1000)
cmd = 'wevtutil qe System /q:"{}" /format:xml'.format(query)

output = subprocess.check_output(cmd, shell=True)

output = '<Events>' + output + '</Events>'
root = ET.fromstring(output)
count = len(root)
status = 'OK' if count == 0 else 'CRITICAL'

print status, '| count.{}.{}={};;;; '.format(LOG_NAME, EVENT_ID, count)
sys.exit(0 if status == 'OK' else 2)
