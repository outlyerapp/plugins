#!/usr/bin/env python
"""
http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/CacheMetrics.WhichShouldIMonitor.html
http://docs.aws.amazon.com/AmazonElastiCache/latest/UserGuide/CacheMetrics.Memcached.html

Returns values for all metrics that exist, if not they are skipped over.
It is worth selecting carefully the metrics you want to reduce the api calls to
cloudwatch.
"""

import datetime
import sys
from boto.ec2 import cloudwatch


AWS_REGION = 'us-east-1'
AWS_KEY = ''
AWS_SECRET = ''
EC_INSTANCE_ID = ''


### Real code
metrics = {
           "CPUUtilization": {"type":"float", "value":None, "uom":"%"},
           "SwapUsage": {"type":"float", "value":None, "uom":"B"},
           "FreeableMemory": {"type":"float", "value":None, "uom":"GB"},
           "NetworkBytesIn": {"type":"float", "value":None, "uom":"B"},
           "NetworkBytesOut": {"type":"float", "value":None, "uom":"B"},
           "BytesUsedForCacheItems": {"type":"float", "value":None, "uom":"B"},
           "BytesReadIntoMemcached": {"type":"float", "value":None, "uom":"B"},
           "BytesWrittenOutFromMemcached": {"type":"float", "value":None, "uom": "B"},
           "CasBadval": {"type":"int", "value":None, "uom":""},
           "CasHits": {"type":"int", "value":None, "uom":""},
           "CasMisses": {"type":"int", "value":None, "uom":""},
           "CmdFlush": {"type":"int", "value":None, "uom":""},
           "CmdGet": {"type":"int", "value":None, "uom":""},
           "CmdSet": {"type":"int", "value":None, "uom":""},
           "CurrConnections": {"type":"int", "value":None, "uom":""},
           "CurrItems": {"type":"int", "value":None, "uom":""},
           "DecrHits": {"type":"int", "value":None, "uom":""},
           "DecrMisses": {"type":"int", "value":None, "uom":""},
           "DeleteHits": {"type":"int", "value":None, "uom":""},
           "DeleteMisses": {"type":"int", "value":None, "uom":""},
           "Evictions": {"type":"int", "value":None, "uom":""},
           "GetHits": {"type":"int", "value":None, "uom":""},
           "GetMisses": {"type":"int", "value":None, "uom":""},
           "IncrHits": {"type":"int", "value":None, "uom":""},
           "IncrMisses": {"type":"int", "value":None, "uom":""},
           "Reclaimed": {"type":"int", "value":None, "uom":""},
          }

# "For Memcached 1.4.14, the following additional metrics are provided.
metrics_1414 = {
                "BytesUsedForHash": {"type":"", "value":None, "uom":"B"},
                "CmdConfigGet": {"type":"", "value":None, "uom":""},
                "CmdConfigSet": {"type":"", "value":None, "uom":""},
                "CmdTouch": {"type":"", "value":None, "uom":""},
                "CurrConfig": {"type":"", "value":None, "uom":""},
                "EvictedUnfetched": {"type":"", "value":None, "uom":""},
                "ExpiredUnfetched": {"type":"", "value":None, "uom":""},
                "SlabsMoved": {"type":"", "value":None, "uom":""},
                "TouchHits": {"type":"", "value":None, "uom":""},
                "TouchMisses": {"type":"", "value":None, "uom":""},
               }

calculated_cache = {
                    "NewConnections": {"type":"int", "value":None, "uom":""},
                    "NewItems": {"type":"int", "value":None, "uom":""},
                    "UnusedMemory": {"type":"float", "value":None, "uom":"B"},
                   }

# Configure which metrics:
# possible values: metrics, metrics_1414 calculated_cache
# metrics_1414 are for if you have
FETCH = [ metrics, metrics_1414, calculated_cache ]

# Build the exit message`
message = "OK | "

conn = cloudwatch.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY,
                                     aws_secret_access_key=AWS_SECRET)

end = datetime.datetime.now()
start = end - datetime.timedelta(minutes=5)

for ha in FETCH:
    for k,vh in ha.items():
        try:
            res = conn.get_metric_statistics(60, start, end, k, "AWS/ElastiCache", "Average",
                                           {"CacheClusterId": EC_INSTANCE_ID})
        except Exception, e:
            print "WARN - status err Error running rds_stats: %s" % e.message
            sys.exit(1)
        # deal with the metrics returned
        if len(res) > 0:
            average = res[-1]["Average"] # last item in result set
            if (k == "FreeStorageSpace" or k == "FreeableMemory"):
                average = average / 1024.0**3.0
            if vh["type"] == "float":
                ha[k]["value"] = "%.4f" % average
            if vh["type"] == "int":
                ha[k]["value"] = "%i" % average
            # append them to the nagios output message
            message += "%s=%s%s;;;; " % (k.lower(), vh["value"], vh["uom"])

if message == "OK | ":
    print "CRITICAL - no rds metrics received"
    sys.exit(2)
else:
    print message
