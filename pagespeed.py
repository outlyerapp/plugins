#!/usr/bin/env python

import urllib2
import optparse

try:
    import json
except ImportError:
    import simplejson as json

UNKNOWN = -1
OK = 0
WARNING = 1
CRITICAL = 2

API_URL = 'https://www.googleapis.com/pagespeedonline/v1/runPagespeed?url=%s&key=%s'
API_KEY = ''
HOSTNAME = ''
WARNING_SCORE = 0
CRITICAL_SCORE = 0


def main():
    try:
        request = urllib2.urlopen(API_URL % (HOSTNAME, API_KEY))
    except urllib2.HTTPError, e:
        print 'Error! %s' % e
        raise SystemExit(UNKNOWN)
    data = json.loads(request.read())

    if data.get('error'):
        print 'Error! %s' % data.get('error').get('errors')[0].get('reason')
        raise SystemExit(UNKNOWN)
    _score = data.get('score')
    if _score <= CRITICAL_SCORE:
        print 'Critical! Current score: %s/100' % _score
        raise SystemExit(CRITICAL)
    if _score <= WARNING_SCORE:
        print 'Warning! Current score: %s/100' % _score
        raise SystemExit(WARNING)
    print 'OK! Current score: %s/100' % _score
    raise SystemExit(OK)

parser = optparse.OptionParser()
parser.add_option('-H', '--hostname', dest='hostname')
parser.add_option('-K', '--key', dest='key')
parser.add_option('-w', '--warning', type=float, dest='warning',
                  default=0)
parser.add_option('-c', '--critical', type=float, dest='critical',
                  default=0)
options, args = parser.parse_args()

if not options.hostname or not options.key:
    print 'Critical! Missing parameters'
    raise SystemExit(CRITICAL)

HOSTNAME = options.hostname
API_KEY = options.key
WARNING_SCORE = options.warning
CRITICAL_SCORE = options.critical

main()
