#!/usr/bin/python
import requests

HOST = "localhost"
QUEUES = [""]
QUEUES_VHOST = '%%2f'
USERNAME = "guest"
PASSWORD = "guest"
PORT = "15672"

#url = "http://%s:%s/api/queues/%%2f/%s" % (HOST, PORT, QUEUE)

URL = "http://%s:%s/api/overview" % (HOST, PORT)


def get_data(url):
    r = requests.get(url, auth=(USERNAME, PASSWORD))
    return r.json()

# Get overview stats
overview = get_data("http://%s:%s/api/overview" % (HOST, PORT))

metrics = {}
metrics['total_messages'] = overview['queue_totals']['messages']
metrics['total_messages_rate'] = overview['queue_totals']['messages_details']['rate']
metrics['total_messages_ready'] = overview['queue_totals']['messages_ready']
metrics['total_messages_ready_rate'] = overview['queue_totals']['messages_ready_details']['rate']
metrics['total_messages_unack'] = overview['queue_totals']['messages_unacknowledged']
metrics['total_messages_unack_rate'] = overview['queue_totals']['messages_unacknowledged_details']['rate']
metrics['total_consumers'] = overview['object_totals']['consumers']
metrics['total_queues'] = overview['object_totals']['queues']
metrics['total_exhanges'] = overview['object_totals']['exchanges']
metrics['total_connections'] = overview['object_totals']['connections']
metrics['total_channels'] = overview['object_totals']['channels']

perf_data = "OK | "
for k, v in metrics.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)

print perf_data



