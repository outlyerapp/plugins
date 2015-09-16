#!/usr/bin/env python

"""
http://docs.aws.amazon.com/ElasticLoadBalancing/latest/DeveloperGuide/elb-cloudwatch-metrics.html
"""

import datetime
import sys
from boto.ec2 import cloudwatch


AWS_REGION = ''
AWS_KEY = ''
AWS_SECRET = ''
ELB_NAME = 'tester'
PERIOD = 60
MINUTES = 1 # minutes of data to retrieve


### Real code
metrics = {"HealthyHostCount": {"stat": "Average","type": "int", "value":None, "uom": ""},
           "UnHealthyHostCount": {"stat": "Average", "type": "int", "value":None, "uom": ""},
           "RequestCount": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "Latency": {"stat": "Average", "type": "int", "value":None, "uom": ""},
           "HTTPCode_ELB_4XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "HTTPCode_ELB_5XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "HTTPCode_Backend_2XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "HTTPCode_Backend_3XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "HTTPCode_Backend_4XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "HTTPCode_Backend_5XX": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "BackendConnectionErrors": {"stat": "Sum", "type": "int", "value":None, "uom": ""},
           "SurgeQueueLength": {"stat": "Maximum", "type": "int", "value":None, "uom": ""},
           "SpilloverCount": {"stat": "Sum", "type": "int", "value":None, "uom": ""}
          }

# Build the exit message`
message = "OK | "

conn = cloudwatch.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY,
                                      aws_secret_access_key=AWS_SECRET)

end = datetime.datetime.utcnow()
start = end - datetime.timedelta(minutes=MINUTES)

for k,vh in metrics.items():
    try:
        # print k
        res = conn.get_metric_statistics(PERIOD, start, end, k, "AWS/ELB", vh['stat'],
                                       dimensions={"LoadBalancerName": ELB_NAME})
    except Exception, e:
        print "WARN - status err Error running elb stats: %s" % e.message
        sys.exit(1)
    # deal with the metrics returned
    # print res
    for stat in res:
        message += "%s=%s%s;;;; " % (k.lower(), stat[vh['stat']], vh['uom'])

if message == "OK | ":
    print "CRITICAL - no ELB metrics received"
    sys.exit(2)
else:
    print message
