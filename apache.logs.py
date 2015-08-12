#!/usr/bin/env python

import re
import os
import sys

TMPDIR = '/opt/dataloop/tmp'

## Change these two variables if you are duplicating this script. Otherwise you will overwrite the filepointer held in the tmpfile.
TMPFILE = 'dl-apache-access'
LOGFILE = '/var/log/apache2/access.log'

combined = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'

status_codes={'2xx': 0,
              '3xx': 0,
              '4xx': 0,
              '5xx': 0}


def tmp_file():
    # Ensure the dataloop tmp dir is available
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_offset():
    with open(TMPDIR + '/' + TMPFILE, 'r') as off:
        try:
            offset = int(off.read())
        except:
            # unable to read offset file
            offset = 0
    return offset


def write_offset(offset):
    with open(TMPDIR + '/' + TMPFILE, 'w') as off:
        off.write("%s" % offset)

# Flow
tmp_file()

# Get the last know log file read position
# to mitigate logrotation, if the file is smaller than offset, read the whole
# log file again
position = get_offset()
file_size = os.stat(LOGFILE).st_size
if file_size < position:
    position = 0

with open(LOGFILE) as fp:
    if position > 0:
        fp.seek(position)
    for line in fp.xreadlines():

        regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', combined))
        m = re.match(regex, line)

        try:
            data = m.groupdict()
        except:
            print "Plugin Failed!"
            sys.exit(2)

        code = data['status']
        if code not in status_codes.keys():
            status_codes[code] = 1
        else:
            status_codes[code] += 1
        if code.startswith('2'):
            status_codes['2xx'] += 1
        if code.startswith('3'):
            status_codes['3xx'] += 1
        if code.startswith('4'):
            status_codes['4xx'] += 1
        if code.startswith('5'):
            status_codes['5xx'] += 1                

    write_offset(fp.tell())
    fp.close()

# emit lots of lovely metrics:
message = "OK | "
for k,v in status_codes.iteritems():
    message += "%s=%s;;;; " % (k,v)

print message
sys.exit(0)
