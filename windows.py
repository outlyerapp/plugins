#!/usr/bin/env python
import subprocess
import sys
import re

counters = ['\Memory\Available MBytes',
            '\Memory\Pages/sec',
            '\PhysicalDisk(* *)\% Disk Time',
            '\PhysicalDisk(* *)\Current Disk Queue Length',
            '\PhysicalDisk(* *)\Disk Transfers/sec',
            '\PhysicalDisk(* *)\Disk Bytes/sec',
            '\PhysicalDisk(* *)\Disk Reads/sec',
            '\PhysicalDisk(* *)\Disk Writes/sec',
            '\PhysicalDisk(* *)\Avg. Disk sec/Read',
            '\PhysicalDisk(** *)\Avg. Disk sec/Write',
            '\Processor(* *)\% Processor Time',
            '\Processor(* *)\% Privileged Time',
            '\System\Processor Queue Length',
            '\System\Context Switches/sec',
            '\Network Interface(* *)\Bytes Total/sec']


command = [r'c:\windows\system32\typeperf.exe', '-sc', '1']

try:
    output = subprocess.check_output(command + counters)
except:
    print "connection failure"
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
