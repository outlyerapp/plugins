#!/usr/bin/env python
import subprocess
import sys
import re

'''
details taken from:

http://blogs.technet.com/b/samdrey/archive/2015/01/26/exchange-2013-performance-counters-and-their-thresholds.aspx
'''

counters = ['MSExchange ADAccess Domain Controllers(*)\LDAP Read Time',
            'MSExchange ADAccess Domain Controllers(*)\LDAP Search Time',
            'MSExchange ADAccess Processes(*)\LDAP Read Time',
            'MSExchange ADAccess Processes(*)\LDAP Search Time',
            'Processor(*)\% Processor Time',
            'Processor(*)\% User Time',
            'Processor(*)\% Privileged Time',
            'System\Processor Queue Length (all instances)',
            'Memory\Available Mbytes',
            'Memory\% Committed Bytes In Use',
            '.NET CLR Memory(*)\% Time in GC',
            '.NET CLR Exceptions(*)\# of Excepts Thrown / sec',
            'Network Interface(*)\Packets Outbound Errors',
            'TCPv4\Connections Reset',
            'TCPv6\Connections Reset',
            'MSExchange Database ==> Instances(*)\I/O Database Reads (Attached) Average Latency',
            'MSExchange Database ==> Instances(*)\I/O Log Writes Average Latency',
            'MSExchange Database ==> Instances(*)\I/O Database Writes (Attached) Average Latency',
            'MSExchange Database ==> Instances(*)\I/O Database Reads (Recovery) Average Latency',
            'MSExchange Database ==> Instances(*)\I/O Database Writes (Recovery) Average Latency',
            'ASP.NET\Application Restarts',
            'ASP.NET\Worker Process Restarts',
            'ASP.NET\Request Wait Time',
            'ASP.NET Applications(*)\Requests In Application Queue',
            'MSExchange RpcClientAccess\RPC Averaged Latency',
            'MSExchange RpcClientAccess\RPC Requests',
            'MSExchangeIS Client Type(*)\RPC Average Latency',
            'MSExchangeIS Client Type\RPC Requests',
            'MSExchangeIS Store(*)\RPC Average Latency'
            ]

command = [r'c:\windows\system32\typeperf.exe', '-sc', '1']

try:
    output = subprocess.check_output(command + counters)
except Exception, e:
    print "Plugin Failed!: %s" % e
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
