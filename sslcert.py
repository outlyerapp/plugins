#!/usr/bin/env python

import sys
from OpenSSL import SSL
import socket
import datetime

"""

    Nagios check to test SSL certificate expiration and cname is correct

"""

HOSTNAME = 'www.dataloop.io'
PORT = 443
CN = '*.dataloop.io'
METHOD = 'SSLv23' # Options : (SSLv2|SSLv3|SSLv23|TLSv1) defaults to SSLv23'

WARN = 15  # Threshold for warning alert in days
CRIT = 5   # Threshold for critical alert in days


def get_options():
    options = {'host': HOSTNAME,
               'port': PORT,
               'method': 'SSLv23',
               'critical': CRIT,
               'warning': WARN,
               'cn': CN}
    return options


def main():
    options = get_options()

    # Initialize context
    if options['method'] == 'SSLv3':
        ctx = SSL.Context(SSL.SSLv3_METHOD)
    elif options['method'] == 'SSLv2':
        ctx = SSL.Context(SSL.SSLv2_METHOD)
    elif options['method'] == 'SSLv23':
        ctx = SSL.Context(SSL.SSLv23_METHOD)
    else:
        ctx = SSL.Context(SSL.TLSv1_METHOD)

    # Set up client
    sock = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    sock.connect((options['host'], int(options['port'])))
    # Send an EOF
    try:
        sock.send("\x04")
        sock.shutdown()
        peer_cert = sock.get_peer_certificate()
        sock.close()
    except SSL.Error, e:
        print e

    exit_status = 0
    exit_message = []

    cur_date = datetime.datetime.utcnow()
    cert_nbefore = datetime.datetime.strptime(peer_cert.get_notBefore(), '%Y%m%d%H%M%SZ')
    cert_nafter = datetime.datetime.strptime(peer_cert.get_notAfter(), '%Y%m%d%H%M%SZ')

    expire_days = int((cert_nafter - cur_date).days)

    if cert_nbefore > cur_date:
        if exit_status < 2:
            exit_status = 2
        exit_message.append('C: cert is not valid')
    elif expire_days < 0:
        if exit_status < 2:
            exit_status = 2
        exit_message.append('Expire critical (expired)')
    elif options['critical'] > expire_days:
        if exit_status < 2:
            exit_status = 2
        exit_message.append('Expire critical')
    elif options['warning'] > expire_days:
        if exit_status < 1:
            exit_status = 1
        exit_message.append('Expire warning')
    else:
        exit_message.append('Expire OK')

    exit_message.append('['+str(expire_days)+'d]')

    for part in peer_cert.get_subject().get_components():
        if part[0] == 'CN':
            cert_cn = part[1]

    if options['cn'] != '' and options['cn'].lower() != cert_cn.lower():
        if exit_status < 2:
            exit_status = 2
        exit_message.append(' - CN mismatch')
    else:
        exit_message.append(' - CN OK')

    exit_message.append(' - cn:'+cert_cn)

    print ''.join(exit_message)
    sys.exit(exit_status)

main()