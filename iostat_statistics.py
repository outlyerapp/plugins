#!/usr/bin/env python
"""

iostat statistics,

Read the last set of device data, and parse out the values.  Assumptions:
* A cron job exists that writes periodic updates to /tmp/iostat.status 
 from the output of 'iostat -xdm 60 2'

"""

### Sample data ###
# Linux 2.6.32-431.el6.x86_64 (bel-mysql-003)   11/10/2015  _x86_64_  (24 CPU)
# 
# Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await  svctm  %util
# ... lines omitted ...
# 
# Device:         rrqm/s   wrqm/s     r/s     w/s    rMB/s    wMB/s avgrq-sz avgqu-sz   await  svctm  %util
# sda               0.00    77.87    6.32   31.03     0.03     0.41    24.01     0.01    0.19   0.13   0.48
# dm-0              0.00     0.00    0.00    1.07     0.00     0.00     8.00     0.00    0.17   0.16   0.02
# dm-1              0.00     0.00    0.00    0.00     0.00     0.00     0.00     0.00    0.00   0.00   0.00
# dm-2              0.00     0.00    6.32  104.30     0.03     0.41     8.03     0.03    0.28   0.04   0.47
### ###


import sys, re

iostats = '/tmp/iostat.status'

try:
  # Open up the file
  file = open( iostats, "r")
except:
    print "Plugin Failed! Unable to open %s" % iostats
    sys.exit(2)

found = 0
result = "OK | "

for lines in file.readlines():
  if found  < 2:
    # Skip the first set of Device ... sda sdb ... whatever entries.  The last line 
    # of output from the file is the one we care about. 
    if re.match('^Device:', lines):
      found += 1
      next

  if found > 1:  
    if re.match('Device:', lines):
      next
    if re.match('^sd[a-z]', lines):
      line = re.split('\s+', lines)
      dev = line[0]
      result += "%s.rrqm_per_sec=%s;;;; " % (dev, line[1])
      result += "%s.wrqm_per_sec=%s;;;; " % (dev, line[2])
      result += "%s.reads_per_sec=%s;;;; " % (dev, line[3])
      result += "%s.writes_per_sec=%s;;;; " % (dev, line[4])
      result += "%s.readMB_per_sec=%s;;;; " % (dev, line[5])
      result += "%s.writeMB_per_sec=%s;;;; " % (dev, line[6])
      result += "%s.avg_request_queue_size=%s;;;; " % (dev, line[7])
      result += "%s.avg_queue_length=%s;;;; " % (dev, line[8])
      result += "%s.avg_wait_time=%s;;;; " % (dev, line[9])
      result += "%s.pct_device_utilization=%s%%;;;; " % (dev, line[11])

print result
sys.exit(0)

