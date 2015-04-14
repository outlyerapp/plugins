#!/usr/bin/env python
from boto import ec2
import boto.ec2.cloudwatch as cloudwatch
import datetime
import sys

"""
    Nagios check script to pull out all the billing metrics from AWS Cloudwatch

    Setup:
        Put in your AWS_KEY and AWS_SECRET below. Region must be us-east-1 for billing metrics
"""

AWS_REGION = 'us-east-1'
AWS_KEY = ''
AWS_SECRET = ''

def get_metrics(metrics):

    """
    Get the statistics for 1 or more metrics at a given moment.
    The metric will request the statistics from 18 hours before
    the date argument until the date argument. (18h is to make
    sure at least 1 datapoint is returned).
    Return: a dict with the metric name as key and the value.
    """
    stats = {}
    end = datetime.datetime.now()
    start = end - datetime.timedelta(hours=18)
    #print 'Retrieving statistics from %s to %s.\n' % (start, end)
    for metric in metrics:

        # Get last value from the last day
        datapoints = metric.query(start, end, 'Maximum', None, 3600)
        datapoints = sorted(datapoints, key=lambda datapoint: datapoint[u'Timestamp'], reverse=True)
        value = 0.0
        if len(datapoints) > 0:
            value = (datapoints[0])[u'Maximum']

        #print "%s : %d" % (metric.dimensions, value)

        if u'ServiceName' not in metric.dimensions:

            # Get total charges across accounts

            # If no LinkedAccount - this is total charge across all accounts
            if u'LinkedAccount' not in metric.dimensions:
                stats['total.total'] = value
            else:
                key = "LinkedAccounts.%s.total" % (metric.dimensions[u'LinkedAccount'][0])
                stats[key] = value
        else:

            # Break out service level billing stats per account and total
            if u'LinkedAccount' not in metric.dimensions:
                key = "total.%s" % (metric.dimensions[u'ServiceName'][0])
                stats[key] = value
            else:
                key = "LinkedAccounts.%s.%s" % (metric.dimensions[u'LinkedAccount'][0], metric.dimensions[u'ServiceName'][0])
                stats[key] = value

    return stats

conn = cloudwatch.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET, validate_certs=False)
billing_metrics = conn.list_metrics(metric_name=u'EstimatedCharges',namespace=u'AWS/Billing')
stats = get_metrics(billing_metrics)

# Build the exit message`
message = "OK | "

for key,value in stats.items():
    message += "%s=%s$;;;; " % (key, value)

if message == "OK | ":
    print "CRITICAL - no billing metrics received"
    sys.exit(2)
else:
    print message