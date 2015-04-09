#!/usr/bin/env python
import subprocess
import sys

os.environ['LD_LIBRARY_PATH'] = '/lib:/usr/lib:/usr/local/lib'
command = "/usr/bin/varnishstat -1 | awk '{print $1,$2}'"

try:
    status = subprocess.check_output(command, shell=True)
except:
    print "connection failure"
    sys.exit(2)

output = "OK | "
metrics_list = [s.lower().strip() for s in status.splitlines()]
for metric in metrics_list:
    k = metric.split(' ')[0]
    v = metric.split(' ')[1]
    output += k + '=' + v + ';;;; '

print output
sys.exit(0)

