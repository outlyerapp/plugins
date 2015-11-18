#!/usr/bin/env python
import subprocess
import sys
import time

command = "/usr/bin/varnishstat -1 | awk '{print $1,$2}'"


def get_varnish_metrics():
    try:
        status = subprocess.check_output(command, shell=True)
        m = {}
        for line in status.splitlines():
            name = line.split()[0].lower().replace('(', '_').replace(')', '_').replace(',,', '_')
            m[name] = line.split()[1]
        return m

    except Exception, e:
        print "Plugin Failed! %s" % e
        sys.exit(2)


# rate calculation
time_between = 5

metrics_before = get_varnish_metrics()
time.sleep(time_between)
metrics = get_varnish_metrics()

metric_rates = {}
for metric, value in metrics.iteritems():
    if value > metrics_before[metric]:
        metric_rates[metric + '_per_sec'] = (int(value) - int(metrics_before[metric])) / time_between

metrics.update(metric_rates)

# print nagios perf data and exit
output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
sys.exit(0)
