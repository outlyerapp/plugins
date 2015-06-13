#!/usr/bin/python

"""
Update the settings block below
"""

import sys
import requests

# Settings
HOST = "localhost"
QUEUES = [""]
QUEUES_VHOST = '%%2f'
USERNAME = "guest"
PASSWORD = "guest"
PORT = "15672"
URL = "http://%s:%s/api/overview" % (HOST, PORT)

def get_data(url):
    r = requests.get(url, auth=(USERNAME, PASSWORD))
    return r.json()

# Get overview stats
try:
    overview = get_data("http://%s:%s/api/overview" % (HOST, PORT))
except:
    print "Plugin Failed! Unable to connect to http://%s:%s/api/overview" % (HOST, PORT)
    sys.exit(2)

metrics = {}

# Message Stats
metrics['message_stats.publish'] = overview['message_stats']['publish']
metrics['message_stats.publish_rate'] = overview['message_stats']['publish_details']['rate']
metrics['message_stats.deliver_get'] = overview['message_stats']['deliver_get']
metrics['message_stats.deliver_get_rate'] = overview['message_stats']['deliver_get_details']['rate']
metrics['message_stats.confirm'] = overview['message_stats']['confirm']
metrics['message_stats.confirm_rate'] = overview['message_stats']['confirm_details']['rate']
metrics['message_stats.deliver_no_ack'] = overview['message_stats']['deliver_no_ack']
metrics['message_stats.deliver_no_ack_rate'] = overview['message_stats']['deliver_no_ack_details']['rate']

# Queue Totals
metrics['queue_totals.messages'] = overview['queue_totals']['messages']
metrics['queue_totals.rate'] = overview['queue_totals']['messages_details']['rate']
metrics['queue_totals.messages_ready'] = overview['queue_totals']['messages_ready']
metrics['queue_totals.messages_ready_rate'] = overview['queue_totals']['messages_ready_details']['rate']
metrics['queue_totals.unack'] = overview['queue_totals']['messages_unacknowledged']
metrics['queue_totals.unack_rate'] = overview['queue_totals']['messages_unacknowledged_details']['rate']

# Object Totals
metrics['object_totals.consumers'] = overview['object_totals']['consumers']
metrics['object_totals.queues'] = overview['object_totals']['queues']
metrics['object_totals.exhanges'] = overview['object_totals']['exchanges']
metrics['object_totals.connections'] = overview['object_totals']['connections']
metrics['object_totals.channels'] = overview['object_totals']['channels']

perf_data = "OK | "
for k, v in metrics.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)

print perf_data
sys.exit(0)

