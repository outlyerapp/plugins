#!/usr/bin/python
import sys
import requests
from urllib import quote

# Settings
HOST = "localhost"
USERNAME = ""
PASSWORD = ""
PORT = "15672"

overview = requests.get("http://%s:%s/api/overview" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()

metrics = {}

def flatten(structure, key="", path="", flattened=None):
    if flattened is None:
        flattened = {}
    if type(structure) not in (dict, list):
        flattened[((path + ".") if path else "") + key] = structure
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            flatten(item, "%d" % i, path + "." + key, flattened)
    else:
        for new_key, value in structure.items():
            flatten(value, new_key, path + "." + key, flattened)
    return flattened

def get_data(data, segment, prefix):
    message_stats = data[segment]
    return flatten(message_stats, segment, prefix)

def get_overview():
    overview = {}
    resp = requests.get("http://%s:%s/api/overview" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
    overview.update(get_data(resp, 'message_stats', 'overview'))
    overview.update(get_data(resp, 'queue_totals', 'overview'))
    overview.update(get_data(resp, 'object_totals', 'overview'))
    return overview

def get_queue_stats(vhost, queue):
    queue_stats = {}
    if vhost == '/':
        resp = requests.get("http://%s:%s/api/queues/%%2F/%s" % (HOST, PORT, queue), auth=(USERNAME, PASSWORD)).json()
    else:
        resp = requests.get("http://%s:%s/api/queues/%s/%s" % (HOST, PORT, quote(vhost), queue), auth=(USERNAME, PASSWORD)).json()
    try:
        queue_stats.update(get_data(resp, 'message_stats', 'queues.' + queue))
        return queue_stats
    except:
        return {}

def get_vhosts():
    vhosts = []
    resp = requests.get("http://%s:%s/api/vhosts" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
    for vhost in resp:
        vhosts.append(vhost['name'])
    return vhosts
    
def get_queues(vhost):
    queues = []
    resp = requests.get("http://%s:%s/api/queues/%s" % (HOST, PORT, vhost), auth=(USERNAME, PASSWORD)).json()
    for queue in resp:
        queues.append(queue['name'])
    return queues

metrics.update(get_overview())
vhosts = get_vhosts()
for vhost in vhosts:
    queues = get_queues(vhost)
    for queue in queues:
        metrics.update(get_queue_stats(vhost, queue))

perf_data = "OK | "
for k, v in metrics.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)

print perf_data
sys.exit(0)
