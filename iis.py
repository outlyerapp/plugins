#!/usr/bin/env python
import subprocess
import sys

"""
Replace _Total in the counters list below to get metrics for a specific site. E.g. Default Web Site.
To see your list of sites run 'c:\windows\system32\inetsrv\appcmd.exe list sites' from an elevated cmd prompt
"""

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
    print "connection failure"
    sys.exit(2)

perf_data = { 'current_connections': output.splitlines()[2].split(',')[1].replace('"','').strip(),
              'current_anon_users': output.splitlines()[2].split(',')[2].replace('"','').strip(),
              'current_non_anon_users': output.splitlines()[2].split(',')[3].replace('"','').strip(),
              'get_requests_sec': output.splitlines()[2].split(',')[4].replace('"','').strip(),
              'put_requests_sec': output.splitlines()[2].split(',')[5].replace('"','').strip(),
              'post_requests_sec': output.splitlines()[2].split(',')[6].replace('"','').strip()
              }

response = "OK | "
for k, v in perf_data.iteritems():
    response += k + '=' + v + ';;;; '
    
print response
sys.exit(0)
