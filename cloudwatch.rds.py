#!/usr/bin/env python

import datetime
import sys
from boto.ec2 import cloudwatch


AWS_REGION = 'us-east-1'
AWS_KEY = ''
AWS_SECRET = ''
RDS_INSTANCE_ID = ''


### Real code
metrics = {"BinLogDiskUsage": {"type":"float", "value":None, "uom":"B"},
           "CPUUtilization":{"type":"float", "value":None, "uom":"%"},
           "DatabaseConnections":{"type":"int", "value":None, "uom":""},
           "DiskQueueDepth":{"type":"int", "value":None, "uom":""},
           "FreeableMemory":{"type":"float", "value":None, "uom":"GB"},
           "FreeStorageSpace":{"type":"float", "value":None, "uom":"GB"},
           "SwapUsage":{"type":"float", "value":None, "uom":"B"},
           "ReadIOPS":{"type":"int", "value":None, "uom":"c/s"},
           "WriteIOPS":{"type":"int", "value":None, "uom":"c/s"},
           "ReadLatency":{"type":"float", "value":None, "uom":"s"},
           "WriteLatency":{"type":"float", "value":None, "uom":"s"},
           "ReadThroughput":{"type":"float", "value":None, "uom":"B/s"},
           "WriteThroughput":{"type":"float", "value":None, "uom":"B/s"},
           "NetworkReceiveThroughput":{"type":"float", "value":None, "uom":"B"},
           "NetworkTransmitThroughput":{"type":"float", "value":None, "uom":"B"},
          }

# Build the exit message`
message = "OK | "

conn = cloudwatch.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY,
                                     aws_secret_access_key=AWS_SECRET)

end = datetime.datetime.now()
start = end - datetime.timedelta(minutes=5)

for k,vh in metrics.items():
    try:
        res = conn.get_metric_statistics(60, start, end, k, "AWS/RDS", "Average",
                                       {"DBInstanceIdentifier": RDS_INSTANCE_ID})
    except Exception, e:
        print "WARN - status err Error running rds_stats: %s" % e.message
        sys.exit(1)
    # deal with the metrics returned
    if len(res) > 0:
        average = res[-1]["Average"] # last item in result set
        if (k == "FreeStorageSpace" or k == "FreeableMemory"):
            average = average / 1024.0**3.0
        if vh["type"] == "float":
            metrics[k]["value"] = "%.4f" % average
        if vh["type"] == "int":
            metrics[k]["value"] = "%i" % average
        # append them to the nagios output message
        message += "%s=%s%s;;;; " % (k.lower(), vh["value"], vh["uom"])

if message == "OK | ":
    print "CRITICAL - no rds metrics received"
    sys.exit(2)
else:
    print message
