#!/usr/bin/env python
import subprocess
import re
import sys

try:
    out = subprocess.check_output(['/usr/lib/ddb/bin/ddb-admin', 'status'])
except Exception, e:
    print "Plugin Failed! %s" % e
    sys.exit(2)

result = "OK | "
for line in out.split("\n"):
    m = re.match(r"^([^ ]+) : ([0-9]+)", line)
    if m:
        k, v = m.groups()
        if k.split('.')[-1] in ['min', 'median', 'max', 'standard_deviation', 'harmonic_mean', 'geometric_mean', 'arithmetic_mean', 'p50', 'p75', 'p95', 'p99', 'p999']:
            v = str(0.001 * float(v)) + 'ms'
        # At some point we should fix floats reported by dalmatiner
        elif k.split('.')[-1] == 'variance':
            v = 0.000001 * float(v)
        result += "%s=%s;;;; " % (k, v)

print result
sys.exit(0)
