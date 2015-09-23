#!/usr/bin/env python
import sys
import requests
import collections

HOST = 'localhost'
PORT = 9200
BASE_URL = "http://%s:%s" % (HOST, PORT)
LOCAL_URL = "/_nodes/_local"
HEALTH_URL = "/_cluster/health"
STATS_URL = "/_nodes/_local/stats"


def _get_es_stats(url):
    data = requests.get(url)
    if data.status_code == 200:
        stats = data.json()
        return stats
    else:
        raise Exception("Cannot get Elasticsearch version")


def flatten(d, parent_key='', sep='.'):
    items = []
    for key, value in d.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, collections.MutableMapping):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


try:
    es_stats = flatten(_get_es_stats(BASE_URL + STATS_URL))
    es_health = flatten(_get_es_stats(BASE_URL + HEALTH_URL))

    perf_data = "OK | "
    for k, v in es_stats.iteritems():
        if str(v)[0].isdigit():
            k = k.rsplit('.')[2::]
            perf_data += '.'.join(k) + '=' + str(v) + ';;;; '

    for k, v in es_health.iteritems():
        if str(v)[0].isdigit():
            perf_data += str(k) + "=" + str(v) + ';;;; '

    print(perf_data)
    sys.exit(0)

except Exception as e:
    print("Plugin Failed! Exception: " + str(e))
    sys.exit(2)

