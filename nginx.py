#!/usr/bin/env python
import re
import requests
import sys

try:
    resp = requests.get('http://127.0.0.1/nginx_status')
except:
    print "connection failed"
    sys.exit(2)
    
data = resp.text
result = {}

match1 = re.search(r'Active connections:\s+(\d+)', data)
match2 = re.search(r'\s*(\d+)\s+(\d+)\s+(\d+)', data)
match3 = re.search(r'Reading:\s*(\d+)\s*Writing:\s*(\d+)\s*''Waiting:\s*(\d+)', data)

if not match1 or not match2 or not match3:
    raise Exception('Unable to parse %s' % url)
    sys.exit(2)

result['connections'] = int(match1.group(1))
result['accepted'] = int(match2.group(1))
result['handled'] = int(match2.group(2))
result['requests'] = int(match2.group(3))
result['reading'] = int(match3.group(1))
result['writing'] = int(match3.group(2))
result['waiting'] = int(match3.group(3))

perf_data = "OK | "
for k, v in result.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)

print perf_data
sys.exit(0)
