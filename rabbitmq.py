#!/usr/bin/python

from optparse import OptionParser
import urllib2
import json
#import pprint

HOST = ""
QUEUE = ""
USER = "guest"
PASS = "guest"
PORT = "15672"
CRIT = 20000
WARN = 10000


def getOptions():
    arguments = OptionParser()
    arguments.add_option("--host", dest="host", help="Host rabbitmq is running on", type="string", default=HOST)
    arguments.add_option("--queue", dest="queue", help="Name of the queue in inspect", type="string", default=QUEUE)
    arguments.add_option("--username", dest="username", help="RabbitMQ API username", type="string", default=USER)
    arguments.add_option("--password", dest="password", help="RabbitMQ API password", type="string", default=PASS)
    arguments.add_option("--port", dest="port", help="RabbitMQ API port", type="string", default=PORT)
    arguments.add_option("--warning-queue-size", dest="warn_queue", help="Size of the queue to alert as warning",
                         type="int", default=WARN)
    arguments.add_option("--critical-queue-size", dest="crit_queue", help="Size of the queue to alert as critical",
                         type="int", default=CRIT)
    return arguments.parse_args()[0]


options = getOptions()

url = "http://%s:%s/api/queues/%%2f/%s" % (options.host, options.port, options.queue)

# handle HTTP Auth
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
top_level_url = url
password_mgr.add_password(None, top_level_url, options.username, options.password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)

response = None
try:
    request = opener.open(url)
    response = request.read()
    request.close()
except urllib2.HTTPError, e:
    print "Error code %s hitting %s" % (e.code, url)
    exit(1)

data = json.loads(response)

#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(data)

num_messages = data.get("messages")
if num_messages > options.crit_queue or num_messages > options.warn_queue:
    print "%s messages in %s queue" % (num_messages, options.queue)
    exit(1 if num_messages > options.crit_queue else 2)

message_stats = data.get("message_stats")
deliver_details = message_stats.get("deliver_get_details")
rate = deliver_details.get("rate")

print "OK | messages=%s;;;; rate=%s;;;;" % (num_messages, rate)
