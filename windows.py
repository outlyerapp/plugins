#!/usr/bin/env python
import subprocess
import sys
import re

counters = ['\Memory\Available MBytes',
            '\Memory\Pages/sec',
            '\PhysicalDisk(_Total)\% Disk Time',
            '\PhysicalDisk(_Total)\Current Disk Queue Length',
            '\PhysicalDisk(_Total)\Disk Transfers/sec',
            '\PhysicalDisk(_Total)\Disk Bytes/sec',
            '\PhysicalDisk(_Total)\Disk Reads/sec',
            '\PhysicalDisk(_Total)\Disk Writes/sec',
            '\PhysicalDisk(_Total)\Avg. Disk sec/Read',
            '\PhysicalDisk(_Total)\Avg. Disk sec/Write',
            '\Processor(_Total)\% Processor Time',
            '\Processor(_Total)\% Privileged Time',
            '\System\Processor Queue Length',
            '\System\Context Switches/sec']


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
    metric = re.sub('(^[\W_]*)|([\W_]*$)', '', metric)
    value = output.splitlines()[2].split(',')[i].replace('"','').strip()
    perf_data[metric] = value
    i += 1

response = "OK | "
for k, v in perf_data.iteritems():
    response += k + '=' + v + ';;;; '
    
print response
sys.exit(0)
