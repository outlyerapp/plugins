#!/usr/bin/env python

# curl http://localhost:8161/admin/xml/queues.jsp
import requests
import xmltodict

xml = requests.get('http://localhost:8161/admin/xml/queues.jsp').text

obj = xmltodict.parse(xml)

result = {}

for queue in obj['queues']['queue']:
    _name = queue['@name']
    result[_name + '_size'] = queue['stats']['@size']
    result[_name + '_consumer_count'] = queue['stats']['@consumerCount']
    result[_name + '_enqueue_count'] = queue['stats']['@enqueueCount']
    result[_name + '_dequeue_count'] = queue['stats']['@dequeueCount']

output = ''
for k, v in result.iteritems():
    n = "%s=%s;;;; " % (k, v)
    output += n

print "OK | " + output
