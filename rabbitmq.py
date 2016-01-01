#!/usr/bin/python
import sys
import requests
from urllib import quote

# Settings
HOST = "localhost"
USERNAME = "guest"
PASSWORD = "guest"
PORT = "15672"
PROTO = "http"

QUEUE_STATS = False
EXCHANGE_STATS = False
VERIFY_SSL = True


def request_data(path):
    if not VERIFY_SSL: requests.packages.urllib3.disable_warnings()
    return requests.get("%s://%s:%s%s" % (PROTO, HOST, PORT, path),
                        auth=(USERNAME, PASSWORD),
                        timeout=10,
                        verify=VERIFY_SSL).json()


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
    resp = request_data('/api/overview')
    return get_data(resp, 'overview.')


def get_queue_stats(vhost, queue):
    if vhost == '/':
        resp = request_data("/api/queues/%%2F/%s" % queue)
    else:
        resp = request_data("/api/queues/%s/%s" % (quote(vhost), queue))
    return get_data(resp, 'vhost.' + vhost + '.' + 'queue.' + queue + '.')


def get_exchange_stats(vhost, exchange):
    if vhost == '/':
        resp = request_data("/api/exchanges/%%2F/%s" % exchange)
    else:
        resp = request_data("/api/exchanges/%s/%s" % (quote(vhost), exchange))
    return get_data(resp, 'vhost.' + vhost + '.' + 'exchange.' + exchange + '.')


def get_vhosts():
    vhost_names = []
    resp = request_data("/api/vhosts")
    for vhost in resp:
        vhost_names.append(vhost['name'])
    return vhost_names


def get_queues(vhost):
    queue_names = []
    resp = request_data("/api/queues/%s" % vhost)
    for queue in resp:
        queue_names.append(queue['name'])
    return queue_names


def get_exchanges(vhost):
    exchange_names = []
    resp = request_data("/api/exchanges/%s" % vhost)
    for exchange in resp:
        exchange_names.append(exchange['name'])
    return exchange_names

try:
    # overview metrics
    metrics = {}
    metrics.update(get_overview())

    if QUEUE_STATS or EXCHANGE_STATS:
        vhosts = get_vhosts()

    # queue statistics
    if QUEUE_STATS:
        for vhost in vhosts:
            queues = get_queues(vhost)
            for queue in queues:
                metrics.update(get_queue_stats(vhost, queue))

    # exchange statistics
    if EXCHANGE_STATS:
        for vhost in vhosts:
            exchanges = get_exchanges(vhost)
            for exchange in exchanges:
                if exchange: metrics.update(get_exchange_stats(vhost, exchange))

    # nagios format output
    perf_data = "OK | "
    for k, v in metrics.iteritems():
        if is_digit(v): perf_data += "%s=%s;;;; " % (k, round(v, 2))
    print perf_data
    sys.exit(0)

except Exception, e:
    print "Plugin Failed! %s" % e
    sys.exit(2)