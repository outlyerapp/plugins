#!/usr/bin/env python
import requests
import ConfigParser
import io
import sys

# settings
config_file = '/etc/ddb/ddb.conf'


class FakeSecHead(object):
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[section]\n'

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()

try:
    with open(config_file) as f:
        sample_config = f.read()
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(FakeSecHead(io.BytesIO(sample_config)))

    node_name = config.get('section', 'nodename')
except Exception, e:
    print "Plugin Failed! Error reading config file: %s" % e


def query_ddb(p):
    headers = {'Accept': 'application/json'}
    return requests.get("http://localhost:8080/%s" % p, headers=headers).json()


def get_buckets():
    return query_ddb('buckets')


def get_metrics(bucket):
    return query_ddb('buckets/%s' % bucket)

try:
    metrics = {}
    for metric in get_metrics('dalmatinerdb'):
        host = metric.split("'.'")[0].replace("'", '')
        if host == node_name:
            points = query_ddb("?q=SELECT %s BUCKET 'dalmatinerdb' LAST 30s" % metric)['d'][0]['v']
            average_value = float(reduce(lambda x, y: x + y, points) / len(points)) / 1000
            path = '.'.join(metric.split("'.'")[1:]).replace("'", '')
            metrics[path] = str(average_value) + 'ms'
    output = "OK | "
    for k, v in metrics.iteritems():
        output += str(k) + '=' + str(v) + ';;;; '
    print output
    sys.exit(0)

except Exception, e:
    print "Plugin Failed! Error querying metrics: %s" % e
    sys.exit(2)