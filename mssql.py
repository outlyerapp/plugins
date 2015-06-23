#!/usr/bin/env python
import subprocess
import sys
import re

counters = ['\SQLServer:Access Methods\FreeSpace Scans/sec',
            '\SQLServer:Access Methods\Full Scans/sec',
            '\SQLServer:Buffer Manager\Buffer cache hit ratio',
            '\SQLServer:Buffer Manager\Free pages',
            '\SQLServer:Buffer Manager\Page life expectancy',
            '\SQLServer:Latches\Total Latch Wait Time (ms)',
            '\SQLServer:Locks(_Total)\Lock Timeouts/sec',
            '\SQLServer:Locks(_Total)\Lock Wait Time (ms)',
            '\SQLServer:Locks(_Total)\Number of Deadlocks/sec',
            '\SQLServer:Memory Manager\Memory Grants Pending',
            '\SQLServer:Memory Manager\Target Server Memory (KB)',
            '\SQLServer:Memory Manager\Total Server Memory (KB)',
            '\SQLServer:SQL Statistics\Batch Requests/sec',
            '\SQLServer:SQL Statistics\SQL Re-Compilations/sec',
            '\SQLServer:SQL Statistics\SQL Compilations/sec',
            '\SQLServer:General Statistics\User Connections']

command = [r'c:\windows\system32\typeperf.exe', '-sc', '1']

try:
    output = subprocess.check_output(command + counters)
except:
    print "Plugin Failed!"
    sys.exit(2)

s_counters = output.splitlines()[1].split(',')
perf_data = {}
i = 1
for s_counter in s_counters:
    if 'PDH-CSV' not in s_counter:
        metric = s_counter.rsplit('\\', 1)[1].strip('"').lower()
        metric = re.sub('[^0-9a-zA-Z]+', '_', metric).strip('_')
        value = output.splitlines()[2].split(',')[i].replace('"','').strip()
        perf_data[metric] = value
        i += 1

response = "OK | "
for k, v in perf_data.iteritems():
    response += k + '=' + v + ';;;; '
    
print response
sys.exit(0)

