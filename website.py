#!/usr/bin/env python

import argparse
import sys
import time
import re
import urllib2
import socket

version = '1.1'

WEBSITE = "http://www.google.co.uk"

### print status and exit with return code
def exitResult(exitCode, summary):
    httpCode2Nagios = {
        200: 0,
        301: 0,
        302: 0,
        404: 1,
        403: 1
    }
    nagiosStatus2Text = {
        0: "OK",
        1: "WARN",
        2: "CRIT"
    }

    # map status code to exit status
    if status['code'] not in httpCode2Nagios:
        exitCode = 2

    # summary with status code
    if status['code'] and summary:
        summary = "Status %d - %s" % (status['code'], summary)
    elif status['code']:
        summary = "Status %d" % (status['code'])

    # output and exit
    print "{nagiosStatus}: {summary} - {size} bytes in {time:.3f} second response time|time={time:.4f};{warn:.4f};{crit:.4f}; size={size:.2f}B;;;0".format(
        nagiosStatus=nagiosStatus2Text[exitCode],
        summary=summary,
        warn=args.warn,
        crit=args.crit,
        **status
    )

    sys.exit(exitCode)

### parse args
parser = argparse.ArgumentParser(description='This plugin can check http(s) content.')
parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version)
parser.add_argument('-p', '--proxy',
                    help='Proxy to use, e.g. user:pass@proxy:port')
parser.add_argument('-t', '--timeout',
                    help='Timout in seconds')
parser.add_argument('-r', '--regex',
                    help='Search page content for this regex')
parser.add_argument('-s', '--size', nargs=2, metavar=('MIN', 'MAX'),
                    help='Minimum page size required (bytes), Maximum page size required (bytes)')
parser.add_argument('-w', '--warning', dest='warn', type=float, default=0,
                    help='Response time to result in warning status (seconds)')
parser.add_argument('-c', '--critical', dest='crit', type=float, default=0,
                    help='Response time to result in critical status (seconds)')
parser.add_argument('url', default=WEBSITE, nargs='?')
args = parser.parse_args()

# valid URL given?
if not args.url or not re.match(r'^https?://', args.url):
    parser.print_help()
    sys.exit('Valid URL required!')

# warn and crit given?
if bool(args.warn) != bool(args.crit):
    parser.print_help()
    sys.exit('Warning and critical must both be given!')

# warn > crit?
if args.warn > 0.0 and args.warn >= args.crit:
    parser.print_help()
    sys.exit('Warning have to be smaller than critical!')

### use proxy?
if args.proxy:
    opener = urllib2.build_opener(
        urllib2.HTTPHandler(),
        urllib2.HTTPSHandler(),
        urllib2.ProxyHandler({'http': str(args.proxy)}),
        urllib2.ProxyHandler({'https': str(args.proxy)})
    )
    urllib2.install_opener(opener)

### do the request
responseBody = ""
status = {
    'code': None,
    'size': 0,
    'time': time.time(),
}
try:
    timeout = float(args.timeout) if args.timeout else None
    response = urllib2.urlopen(args.url, None, timeout)
    status['code'] = response.getcode()
    responseBody = response.read()

except urllib2.HTTPError as e:
    status['code'] = e.code
    exitResult(2, e)

except urllib2.URLError as e:
    exitResult(2, str(e.reason))

except socket.timeout as e:
    exitResult(2, "Socket timeout")


# save some status data
status['size'] = len(responseBody)
status['time'] = time.time() - status['time']


### check body content?
if args.regex and not re.search(args.regex, responseBody, re.IGNORECASE):
    exitResult(2, "Pattern not found")

### check page size?
if args.size:
    args.size = map(int, args.size)
    if status['size'] < args.size[0]:
        exitResult(2, "pagesize to small")
    if status['size'] > args.size[1]:
        exitResult(2, "pagesize to large")

### check response time?
if args.crit and status['time'] > float(args.crit):
    exitResult(2, "Response to slow")
elif args.warn and status['time'] > float(args.warn):
    exitResult(1, "Response to slow")

### output status and return status
exitResult(0, "")
