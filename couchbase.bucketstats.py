#!/usr/bin/env python
"""
Update the USER, PASSWORD and BUCKET variables below.
"""

import sys
import requests
from requests.auth import HTTPBasicAuth

USER = ''
PASSWORD = ''
BUCKET = ''

url = 'http://localhost:8091/pools/default/buckets/%s/stats'
output = "OK | "
exit_status = 0
auth = HTTPBasicAuth(USER, PASSWORD)
perf_data = {}

try:
    default = requests.get('http://localhost:8091/pools/default/buckets/%s/stats' % BUCKET, auth=auth, timeout=60).json()
except:
    print "Plugin Failed! Unable to connect to http://localhost:8091/pools/default/buckets/%s/stats" % BUCKET
    sys.exit(2)
    
samples = default['op']['samples']


def average_list(l):
    return reduce(lambda x, y: x + y, l) / float(len(l))

for k, v in samples.iteritems():
    if 'views/' not in k and 'proc/' not in k:
        output += str(k) + '=' + str(average_list(v)) + ';;;; '
        
print output
sys.exit(0)
