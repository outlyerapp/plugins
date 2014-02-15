#!/usr/bin/env python

import re
import sys
import socket
from urllib2 import urlopen, URLError
from json import loads
from optparse import OptionParser

RIAK_HOST = ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1])[0]
RIAK_PORT = 8098


def _nagios(hdr, msg, code):
    print '%s: %s' % (hdr, msg)
    return code


def critical(msg):
    return _nagios('CRITICAL', msg, 2)


def warning(msg):
    return _nagios('WARNING', msg, 1)


def okay(msg):
    return _nagios('OKAY', msg, 0)


def main():
    parser = OptionParser()
    parser.add_option('-H', '--host', dest='host', default=RIAK_HOST,
                      help='Host to connect to.', metavar='HOST')
    parser.add_option('-p', '--port', dest='port', type='int', default=RIAK_PORT,
                      help='Port to connect to.', metavar='PORT')
    parser.add_option('--95th', dest='t95', metavar='THRESHOLDS', default='15,25,5,10',
                      help='"PW,PC,GW,GC" values for 95th percentile data')
    parser.add_option('--99th', dest='t99', metavar='THRESHOLDS', default='50,100,25,50',
                      help='"PW,PC,GW,GC" values for 99th percentile data')
    parser.add_option('--100th', dest='t100', metavar='THRESHOLDS', default='50,100,25,50',
                      help='"PW,PC,GW,GC" values for 100th percentile data')
    parser.add_option('--mean', dest='tmean', metavar='THRESHOLDS', default='50,100,25,50',
                      help='"PW,PC,GW,GC" values for mean percentile data')
    parser.add_option('--median', dest='tmedian', metavar='THRESHOLDS', default='50,100,25,50',
                      help='"PW,PC,GW,GC" values for median percentile data')
    parser.add_option('--95th-objsize', dest='o95', metavar='THRESHOLDS', default='150000,600000',
                      help='"W,C" values for 95th percentile data')
    parser.add_option('--99th-objsize', dest='o99', metavar='THRESHOLDS', default='150000,600000',
                      help='"W,C" values for 99th percentile data')
    parser.add_option('--100th-objsize', dest='o100', metavar='THRESHOLDS', default='150000,600000',
                      help='"W,C" values for 100th percentile data')
    parser.add_option('--mean-objsize', dest='omean', metavar='THRESHOLDS', default='150000,600000',
                      help='"W,C" values for mean percentile data')
    parser.add_option('--median-objsize', dest='omedian', metavar='THRESHOLDS', default='150000,600000',
                      help='"W,C" values for median percentile data')
    parser.add_option('--95th-siblings', dest='s95', metavar='THRESHOLDS', default='3,6',
                      help='"W,C" values for 95th percentile data')
    parser.add_option('--99th-siblings', dest='s99', metavar='THRESHOLDS', default='3,6',
                      help='"W,C" values for 99th percentile data')
    parser.add_option('--100th-siblings', dest='s100', metavar='THRESHOLDS', default='3,6',
                      help='"W,C" values for 100th percentile data')
    parser.add_option('--mean-siblings', dest='smean', metavar='THRESHOLDS', default='3,6',
                      help='"W,C" values for mean percentile data')
    parser.add_option('--median-siblings', dest='smedian', metavar='THRESHOLDS', default='3,6',
                      help='"W,C" values for median percentile data')
    parser.add_option('--nodes', dest='tnodes', metavar='NODE_THRESHOLDS', default='0,0',
                      help='"W,C" format for connected node thresholds')
    (options, args) = parser.parse_args()

    types = ('95', '99', '100', 'mean', 'median')
    for optname in types:
        val = getattr(options, 't%s' % optname, None)
        if val is not None and not re.match(r'^\d+,\d+,\d+,\d+$', val):
            parser.error('Latency thresholds must be of the format "PW,PC,GW,GC".')
        val = getattr(options, 's%s' % optname, None)
        if val is not None and not re.match(r'^\d+,\d+$', val):
            parser.error('Sibling thresholds must be of the format "W,C".')
        val = getattr(options, 'o%s' % optname, None)
        if val is not None and not re.match(r'^\d+,\d+$', val):
            parser.error('Object size thresholds must be of the format "W,C".')
    if options.tnodes and not re.match(r'^\d+,\d+$', options.tnodes):
        parser.error('Connected node threshold must be of the format "W,C".')

    try:
        req = urlopen("http://%s:%d/stats" % (options.host, options.port))
        obj = loads(req.read())
    except (URLError, ValueError) as e:
        return critical(str(e))

    crit, warn, ok = [], [], []
    def check_ms(metric, warning, critical):
        if metric not in obj:
            crit.append('%s not found in Riak stats output' % metric)
            return
        val_ms = int(obj[metric] / 1000)
        if val_ms > critical:
            crit.append('%s: %dms (>%dms)' % (metric, val_ms, critical))
        elif val_ms > warning:
            warn.append('%s: %dms (>%dms)' % (metric, val_ms, warning))
        else:
            ok.append('%s: %dms' % (metric, val_ms))

    for ttype in types:
        val = getattr(options, 't%s' % ttype, None)
        if val is None:
            continue
        pw, pc, gw, gc = [int(x) for x in val.split(',', 4)]
        check_ms('node_get_fsm_time_%s' % ttype, gw, gc)
        check_ms('node_put_fsm_time_%s' % ttype, pw, pc)

    def check(metric, warning, critical):
        if metric not in obj:
            crit.append('%s not found in Riak stats output' % metric)
            return
        val = int(obj[metric])
        if val > critical:
            crit.append('%s: %d (>%d)' % (metric, val, critical))
        elif val > warning:
            warn.append('%s: %d (>%d)' % (metric, val, warning))
        else:
            ok.append('%s: %d' % (metric, val))

    for ptuple in (('o', 'objsize'), ('s', 'siblings')):
        prefix, stat = ptuple
        for ttype in types:
            val = getattr(options, '%s%s' % (prefix, ttype), None)
            if val is None:
                continue
            w, c = [int(x) for x in val.split(',', 2)]
            check('node_get_fsm_%s_%s' % (stat, ttype), w, c)

    val = getattr(options, 'tnodes', None)
    if val is not None:
        rw, rc = [int(x) for x in val.split(',', 2)]
        if 'connected_nodes' in obj:
            conn_nodes = len(obj['connected_nodes'])
            if conn_nodes < rc:
                crit.append('nodes: %d connected (<%d)' % (conn_nodes, rc))
            elif conn_nodes < rw:
                warn.append('nodes: %d connected (<%d)' % (conn_nodes, rw))
            else:
                ok.append('nodes: %d connected' % conn_nodes)
        else:
            crit.append('nodes: unable to determine connected nodes')

    if len(crit) > 0:
        return critical(', '.join(crit))
    elif len(warn) > 0:
        return warning(', '.join(warn))
    return okay(', '.join(ok))

print sys.exit(main())
