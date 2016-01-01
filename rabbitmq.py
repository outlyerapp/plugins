#!/usr/bin/python
import sys
import requests
from urllib import quote

# Settings
HOST = "localhost"
USERNAME = ""
PASSWORD = ""
PORT = "15672"

try:
    overview = requests.get("http://%s:%s/api/overview" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
except Exception, e:
    print "Plugin Failed! %s" % e
    
metrics = {}


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
    overview = {}
    resp = requests.get("http://%s:%s/api/overview" % (HOST, PORT), auth=(USERNAME, PASSWORD)).json()
    overview.update(get_data(resp, 'overview.'))
    overview.update(get_data(resp, 'overview.'))
    overview.update(get_data(resp, 'overview.'))
    return overview

def get_queue_stats(vhost, queue):
    queue_stats = {}
    if vhost == '/':
        resp = requests.get("http://%s:%s/api/queues/%%2F/%s" % (HOST, PORT, queue), auth=(USERNAME, PASSWORD)).json()
    else:
        resp = requests.get("http://%s:%s/api/queues/%s/%s" % (HOST, PORT, quote(vhost), queue), auth=(USERNAME, PASSWORD)).json()
    try:
        queue_stats.update(get_data(resp, 'queues.' + queue + '.'))
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
    if is_digit(v):
        perf_data += "%s=%s;;;; " % (k, round(v, 2))

print perf_data
sys.exit(0)

