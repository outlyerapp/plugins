#!/usr/bin/env python

import sys
import urllib2
from optparse import OptionParser

URL = "http://localhost"

# Nagios exit codes
UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

parser = OptionParser()
parser.add_option('-u', '--url', default=URL, dest='url')

options, args = parser.parse_args()

if not getattr(options, 'url'):
    print 'CRITICAL - %s not specified' % options.url
    sys.exit(CRITICAL)

address = options.url+"/haproxy?stats;csv"

conn = urllib2.urlopen(address)
stats = conn.read()
conn.close()

row = [[]]
field = ""
j = 0

for i in stats:
    if i == "\n":
        j += 1
        row.append([])
    elif i == ",":
        row[j].append(field)
        field = ""
    else:
        field += i

print "number of connections: %s :: Monitored: %s %s %s/%s  %s %s %s/%s" % (row[1][4],
                                                                            row[6][0],
                                                                            row[6][17],
                                                                            row[6][18],
                                                                            row[6][19],
                                                                            row[9][0],
                                                                            row[9][17],
                                                                            row[9][18],
                                                                            row[9][19])
total = 0
if total < 12:
    sys.exit(OK)
elif 12 < total < 18:
    sys.exit(WARNING)
else:
    sys.exit(CRITICAL)
