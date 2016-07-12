#!/usr/bin/env python
import os
import sys
from datetime import datetime

LOGFILE = '/var/log/mail.log'

now = datetime.now()

states = {'deferred': 0,
          'sent': 0,
          'bounced': 0}


def reverse_read(file_name, separator=os.linesep):
    with file(file_name) as f:
        f.seek(0, 2)
        file_size = f.tell()
        r_cursor = 1
        while r_cursor <= file_size:
            a_line = ''
            while r_cursor <= file_size:
                f.seek(-1 * r_cursor, 2)
                r_cursor += 1
                c = f.read(1)
                if c == separator and a_line:
                    r_cursor -= 1
                    break
                a_line += c
            a_line = a_line[::-1]
            yield a_line

for line in reverse_read(LOGFILE):
    split_line = line.split(' ')
    line_date = ' '.join(split_line[:4])
    line_time = datetime.strptime(line_date, '%b  %d %H:%M:%S').replace(year=now.year)
    delta = now - line_time
    if delta.seconds < 30:
        if len(split_line) > 12:
            if 'status=sent' in split_line[12]:
                states['sent'] += 1
            if 'status=deferred' in split_line[12]:
                states['deferred'] += 1
            if 'status=bounced' in split_line[12]:
                states['bounced'] += 1
    else:
        break

message = "OK | "
for k, v in states.iteritems():
    message += "%s=%s;;;; " % (k, v)
print message
sys.exit(0)