#!/usr/bin/python
import sys
import requests
from urllib import quote

# Settings
HOST = "localhost"
USERNAME = ""
PASSWORD = ""
PORT = "15672"
QUEUE_STATS = False


def flatten(d, result=None):
    if result is None:
        result = {}
    for key in d:
        value = d[key]
        if isinstance(value, dict):
            value1 = {}
            for keyIn in value:
                value1[".".join([key,keyIn])]=value[keyIn]
            flatten(value1, result)
        elif isinstance(value, (list, tuple)):
            for indexB, element in enumerate(value):
                if isinstance(element, dict):
                    value1 = {}
                    index = 0
                    for keyIn in element:
                        newkey = ".".join([key,keyIn])
                        value1[".".join([key,keyIn])]=value[indexB][keyIn]
                        index += 1
                    for keyA in value1:
                        flatten(value1, result)
        else:
            result[key]=value
    return result


def is_digit(d):
    if isinstance(d, bool):
        return False
    elif isinstance(d, int) or isinstance(d, float):
        return True
    return False


def prepend_dict(d, s):
    return dict(map(lambda (key, value): (s + str(key), value), d.items()))


def get_data(data, prefix):
    flattened_data = flatten(data)
    appended_data = prepend_dict(flattened_data, prefix)
    return appended_data


def get_overview():
    resp = requests.get("http://%s:%s/api/overview" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
    return get_data(resp, 'overview.')


def get_queue_stats(vhost, queue):
    if vhost == '/':
        resp = requests.get("http://%s:%s/api/queues/%%2F/%s" % (HOST, PORT, queue), auth=(USERNAME, PASSWORD)).json()
    else:
        resp = requests.get("http://%s:%s/api/queues/%s/%s" % (HOST, PORT, quote(vhost), queue), auth=(USERNAME, PASSWORD)).json()
    return get_data(resp, 'queues.' + queue + '.')


def get_vhosts():
    vhost_names = []
    resp = requests.get("http://%s:%s/api/vhosts" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
    for vhost in resp:
        vhost_names.append(vhost['name'])
    return vhost_names


def get_queues(vhost):
    queue_names = []
    resp = requests.get("http://%s:%s/api/queues/%s" % (HOST, PORT, vhost), auth=(USERNAME, PASSWORD)).json()
    for queue in resp:
        queue_names.append(queue['name'])
    return queue_names

try:
    # overview metrics
    metrics = {}
    metrics.update(get_overview())

    # queue statistics
    if QUEUE_STATS:
        vhosts = get_vhosts()
        for vhost in vhosts:
            queues = get_queues(vhost)
            for queue in queues:
                metrics.update(get_queue_stats(vhost, queue))

    # nagios format output
    perf_data = "OK | "
    for k, v in metrics.iteritems():
        if is_digit(v):
            perf_data += "%s=%s;;;; " % (k, round(v, 2))
    print perf_data
    sys.exit(0)

except Exception, e:
    print "Plugin Failed! %s" % e
    sys.exit(2)