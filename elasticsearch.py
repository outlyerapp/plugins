#!/usr/bin/env python

import sys
import requests
import collections

"""
Hit up the nodes stats url and pull back all the metrics for that node
TODO: clean up some of the kv pairs coming back and exclude the non-numeric
values (some come back as mb and have a byte equiv key
"""


HOST = 'localhost'
PORT = 9200

BASE_URL = "http://%s:%s" % (HOST, PORT)
HEALTH_URL = "/_cluster/health"
NODES_URL = "/_nodes/stats?all=true"


def _get_es_stats(url):
    """ Get the node stats
    """
    data = requests.get(url)
    if data.status_code == 200:
        stats = data.json()
        return stats
    else:
        raise Exception("Cannot get Elasticsearch version")


def flatten(d, parent_key='', sep='.'):
    """ flatten a dictionary into a dotted string
    """
    items = []
    for key, value in d.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, collections.MutableMapping):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


try:
    es_stats = flatten(_get_es_stats(BASE_URL + NODES_URL))
    es_health = flatten(_get_es_stats(BASE_URL + HEALTH_URL))

    all_stats = dict(es_stats.items() + es_health.items())

    #print all_stats

    perf_data = "OK | "
    for k, v in all_stats.iteritems():
        if str(v)[0].isdigit():
            k = k.rsplit('.')[2::]
            perf_data += '.'.join(k) + '=' + str(v) + ';;;; '

    print(perf_data)
    sys.exit(0)

except Exception as e:
    print("Exception: " + str(e))
    sys.exit(2)
