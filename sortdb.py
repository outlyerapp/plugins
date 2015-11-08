#!/usr/bin/env python
import sys
import requests
import socket
import os
import json
from datetime import datetime

server = socket.getfqdn()
port = 9875

no_rates = ['db_mtime', 'db_size', 'fwmatch_95', 'fwmatch_99', 'fwmatch_average_request', 'get_95',
            'get_99', 'get_average_request', 'mget_95', 'mget_99', 'mget_average_request',
            'range_95', 'range_99', 'range_average_requests', 'fwmatch_hitrate', 'get_hitrate', 'mget_hitrate',
            'range_hitrate']

TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'sortdb.json'
TIMESTAMP = datetime.now().strftime('%s')


def get_metrics():

    url = 'http://%s:%d/stats' % (server, port)
    metrics = {}

    try:
        resp = requests.get(url).json()

        for _k, _v in resp.iteritems():
            metrics[_k] = _v

        metrics['fwmatch_hitrate'] = (metrics['fwmatch_misses'] + 1) / (metrics['fwmatch_hits'] + 1) * 100
        metrics['get_hitrate'] = (metrics['get_misses'] + 1) / (metrics['get_hits'] + 1) * 100
        metrics['mget_hitrate'] = (metrics['mget_misses'] + 1) / (metrics['mget_hits'] + 1) * 100
        metrics['range_hitrate'] = (metrics['range_misses'] + 1) / (metrics['range_hits'] + 1) * 100

    except requests.ConnectionError, e:
        print "connection failed: %s" % e
        sys.exit(2)

    except Exception, e:
        print "Stats collection failed: %s" % e
        sys.exit(2)

    return metrics


'''Rate Calculation Functions'''


def tmp_file():
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_cache():
    with open(TMPDIR + '/' + TMPFILE, 'r') as json_fp:
        try:
            json_data = json.load(json_fp)
        except Exception, e:
            print "not a valid json file. rates calculations impossible: %s" % e
            json_data = []
    return json_data


def write_cache(cache):
    with open(TMPDIR + '/' + TMPFILE, 'w') as json_fp:
        try:
            json.dump(cache, json_fp)
        except Exception, e:
            print "unable to write cache file, future rates will be hard to calculate: %s" % e


def cleanse_cache(cache):
    try:
        # keep the cache at a max of 1 hour of data
        while (int(TIMESTAMP) - int(cache[0]['timestamp'])) >= 3600:
            cache.pop(0)
        # keep the cache list to 120
        while len(cache) >= 120:
            cache.pop(0)
        return cache

    except Exception, e:
        os.remove(TMPDIR + '/' + TMPFILE)
        print "failed to cleanse cache: %s" % e


def calculate_rates(data_now, json_data, rateme):
    # Assume last value gives up to an hour's worth of stats
    # i.e. 120 values stored every 30 secs
    # pop the first value off our cache and calculate the rate over the time period
    if len(json_data) > 1:
        try:
            history = json_data[0]
            seconds_diff = int(TIMESTAMP) - int(history['timestamp'])
            rate_diff = float(data_now[rateme]) - float(history[rateme])
            data_per_second = "{0:.2f}".format(rate_diff / seconds_diff)
            return data_per_second

        except Exception, e:
            print "failed to calculate rates!: %s" % e
            return None


'''Main Program'''


# Ensure the tmp dir and file exist
tmp_file()

# Get our cache of data
data = get_cache()

# If the cache has data then update it
if len(data) > 0:
    data = cleanse_cache(data)

# Get the metrics
result = get_metrics()

# Calculate rates
all_rates = list(result.keys())

rates = list(set(all_rates) - set(no_rates))

for rate in rates:
    _ = calculate_rates(result, data, rate)
    if _ is not None:
        result[rate + "_per_sec"] = _

# Append to the cache and write out for the next pass
dated_result = result
dated_result['timestamp'] = TIMESTAMP
data.append(dated_result)
write_cache(data)

# Exit with performance data
perf_data = "OK | "
for k, v in result.iteritems():
    try:
        _ = float(v)
        perf_data += "%s=%s;;;; " % (k, v)
    except ValueError:
        continue

print perf_data
sys.exit(0)