#!/usr/bin/env python

import argparse
import sys
import re
from OpenSSL import SSL
import socket
import datetime

version = '1.0'


### print status and exit with return code
def exitResult(nbefore, nafter):
    nagiosStatus2Text = {
        0: "OK",
        1: "WARN",
        2: "CRIT"
    }

    now = datetime.datetime.utcnow()
    if now > nafter:
        diff = now - nafter
    else:
        diff = nafter - now

    expire = {
        'days': int(diff.days),
        'minutes': int(diff.seconds/60),
        'hours': int(diff.seconds/60/60),
        'expired': nafter < now,
        'date': nafter,
    }
    exitCode = 2

    # invalid
    if nbefore > now:
        summary = "Certificate is invalid"

    # expired
    elif expire['expired']:
        summary = "Certificate expired {days} days ago".format(**expire)

    # crit...
    elif args.crit and args.crit > expire['days']:
        if expire['days'] > 0:
            summary = "Certificate expire in {days} days".format(**expire)
        elif expire['hours'] > 1:
            summary = "Certificate expire in {hours} hours".format(**expire)
        else:
            summary = "Certificate expire in {minutes} minutes".format(**expire)

    # warn...
    elif args.warn and args.warn > expire['days']:
        summary = "Certificate expire in {days} days".format(**expire)
        exitCode = 1

    # ok	
    else:
        summary = "Certificate expire {date:%Y-%m-%d, %H:%M} UTC".format(**expire)
        exitCode = 0

    # output and exit
    print "{nagiosStatus}: {summary}|days={days:d};{warn:d};{crit:d};0".format(
        nagiosStatus=nagiosStatus2Text[exitCode],
        summary=summary,
        warn=args.warn,
        crit=args.crit,
        **expire
    )

    sys.exit(exitCode)

### parse args
parser = argparse.ArgumentParser(description='This plugin can check ssl certificates.')
parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version)
parser.add_argument('-p', '--proxy',
                    help='Proxy to use, e.g. proxy:port or user:pass@proxy:port')
parser.add_argument('-t', '--timeout',
                    help='Timout in seconds')
parser.add_argument('-w', '--warning', dest='warn', type=int, default=30,
                    help='Days until certificate expires to be in warning-state. (Default: 30)')
parser.add_argument('-c', '--critical', dest='crit', type=int, default=0,
                    help='Days until certificate expires to be in critical-state. (Default: 0)')
parser.add_argument('domain', nargs='?')
args = parser.parse_args()

# domain given?
if not args.domain:
    parser.print_help()
    sys.exit('Domain required!')

### create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(args.timeout)

### use proxy?
if args.proxy:
    proxy = re.search(r'^(?:([^:]+):([^:]*)@)?([^:]+):(.*)$', args.proxy).groups()
    s.connect((proxy[2], int(proxy[3])))
    CONNECT = "CONNECT %s HTTP/1.0\r\nConnection: close\r\n\r\n" % (args.domain)
    s.send(CONNECT)
    s.recv(4096)
else:
    s.connect((args.domain, 443))

### send request
ctx = SSL.Context(SSL.SSLv23_METHOD)
ss = SSL.Connection(ctx, s)
ss.set_connect_state()
ss.do_handshake()

### parse cert
cert = ss.get_peer_certificate()
cert_nbefore = datetime.datetime.strptime(cert.get_notBefore(), '%Y%m%d%H%M%SZ')
cert_nafter = datetime.datetime.strptime(cert.get_notAfter(), '%Y%m%d%H%M%SZ')
exitResult(cert_nbefore, cert_nafter)

### close socket
ss.shutdown()
ss.close()
