#!/usr/bin/env python

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


def _get_es_version(url):
    """ Get the running version of Elasticsearch
    """
    data = requests.get(url)
    if data.status_code == 200:
        # print data.json()
        version = data.json()['version']['number']
        return version
    else:
        raise Exception("Cannot get Elasticsearch version")


def _get_es_stats(url):
    """ Get the node stats
    """
    data = requests.get(url)
    if data.status_code == 200:
        # print data.json()
        stats = data.json()
        return stats
    else:
        raise Exception("Cannot get Elasticsearch version")


def flatten(d, parent_key='', sep='.'):
    """ flatten a dictionary into a dotted string
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


try:
    es_ver = _get_es_version(BASE_URL)
    # print es_ver

    es_stats = _get_es_stats(BASE_URL + NODES_URL)
    # print es_stats

    es_stats_flat = flatten(es_stats)

    perf_data = "OK | "
    for k,v in es_stats_flat.iteritems():
        k = k.rsplit('.')[2::]
        perf_data +=  'elasticsearch.' + '.'.join(k) + '=' + str(v) + ';;;; '

    print(perf_data)

except Exception as e:
    print("Exception: " + str(e))
