#!/usr/bin/env python

import requests
import xmltodict
from datetime import datetime

USER = ''
PASSWORD = ''
TIME = 3600 # age metric defaults to hours. set to 60 for minutes

xml = requests.get('http://%s:%s@localhost:8161/admin/xml/queues.jsp' % (USER, PASSWORD)).text
obj = xmltodict.parse(xml)

result = {}
now = datetime.now()

for queue in obj['queues']['queue']:
    _name = queue['@name'].lower()
    _feed = queue['feed']['atom']
    result[_name + '_size'] = queue['stats']['@size']
    result[_name + '_consumer_count'] = queue['stats']['@consumerCount']
    result[_name + '_enqueue_count'] = queue['stats']['@enqueueCount']
    result[_name + '_dequeue_count'] = queue['stats']['@dequeueCount']
    feed_xml = requests.get('http://%s:%s@localhost:8161/admin/' % (USER, PASSWORD) + _feed + '&maxMessages=1').text
    try:
        feed_obj = xmltodict.parse(feed_xml)['feed']['entry']
        published = datetime.strptime(feed_obj['published'], "%Y-%m-%dT%H:%M:%SZ")
        age = (now - published).total_seconds() / TIME
        result[_name + '.age'] = age
    except:
        pass


output = ''
for k, v in result.iteritems():
    n = "%s=%s;;;; " % (k, v)
    output += n

print "OK | " + output
