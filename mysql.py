#!/usr/bin/env python
import subprocess
import re
import sys

status = subprocess.check_output(['/usr/local/bin/mysqladmin', 'status'])
status = re.sub(': ', '=', status)
status = re.sub('  ', ';;;; ', status)

print 'OK | %s' % status
sys.exit(0)
