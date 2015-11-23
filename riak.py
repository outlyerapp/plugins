#!/usr/bin/env python
import sys
import requests
from socket import gethostname

URL = 'http://%s:8098/stats' % gethostname()

try:
    resp = requests.get(URL).json()
except Exception, e:
    print "connection failed: %s" % e
    sys.exit(2)


result = "OK | "
for k, v in resp.iteritems():
    if isinstance(v, int) or isinstance(v, float):
            if 'time' in k:
                result += str(k) + '=' + str(v/1000) + 'ms;;;; '
            else:
                result += str(k) + '=' + str(v) + ';;;; '

print result
sys.exit(0)