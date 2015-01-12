#!/usr/bin/env python
import subprocess
import re
import sys

"""
Open the mysql console on the server and run:
    grant usage on *.* to 'dataloop'@'localhost' identified by 'dataloop';

Or alternatively change the -udataloop and -pdataloop to a mysql user that can run the status command
"""
try:
    status = subprocess.check_output(['/usr/bin/mysqladmin', '-udataloop', '-pdataloop', 'status'])
    status = re.sub(': ', '=', status)
    status = re.sub('  ', ';;;; ', status)
except:
    sys.exit(2)

print 'OK | %s' % status
sys.exit(0)

