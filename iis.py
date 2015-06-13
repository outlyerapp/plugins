#!/usr/bin/env python
"""
Replace _Total in the counters list below to get metrics for a specific site. E.g. Default Web Site.
To see your list of sites run 'c:\windows\system32\inetsrv\appcmd.exe list sites' from an elevated cmd prompt
"""

import subprocess
import sys
import re

counters = ['\Web Service(_Total)\Current Connections',
            '\Web Service(_Total)\Current Anonymous Users',
            '\Web Service(_Total)\Current NonAnonymous Users',
            '\Web Service(_Total)\Get Requests/sec',
            '\Web Service(_Total)\Put Requests/sec',
            '\Web Service(_Total)\Post Requests/sec'
            ]
            
command = [r'c:\windows\system32\typeperf.exe', '-sc', '1']

try:
    output = subprocess.check_output(command + counters)
except:
    print "Plugin Failed!"
    sys.exit(2)
    
perf_data = {}
i = 1
for counter in counters:
    metric = counter.split('\\')[2].lower()
    metric = re.sub('[^0-9a-zA-Z]+', '_', metric)
    value = output.splitlines()[2].split(',')[i].replace('"','').strip()
    perf_data[metric] = value
    i += 1

response = "OK | "
for k, v in perf_data.iteritems():
    response += k + '=' + v + ';;;; '
    
print response
sys.exit(0)
