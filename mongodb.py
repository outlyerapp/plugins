#!/usr/bin/env python

import subprocess

ps = subprocess.Popen(('mongostat', '-n', '1', '--noheaders'), stdout=subprocess.PIPE)
output = subprocess.check_output(('tail', '-1'), stdin=ps.stdout)
ps.wait()

metrics = output.split()

insert = metrics[0].replace('*', '')
query = metrics[1].replace('*', '')
update = metrics[2].replace('*', '')
delete = metrics[3].replace('*', '')
getmore = metrics[4]
command = metrics[5].split('|')[0]
flushes = metrics[6]
mapped = metrics[7]
vsize = metrics[8]
res = metrics[9]
faults = metrics[10]
locked = metrics[11].replace('local:', '')
miss = metrics[12]
qrqw = metrics[13].split('|')[0]
araw = metrics[14].split('|')[0]
net_in = metrics[15]
net_out = metrics[16]
connections = metrics[17]

print "OK | insert=%s;;;; query=%s;;;; update=%s;;;; delete=%s;;;; getmore=%s;;;; command=%s;;;; " \
      "flushes=%s;;;; mapped=%s;;;; vsize=%s;;;; res=%s;;;; faults=%s;;;; locked=%s;;;; " \
      "miss=%s;;;; qrqw=%s;;;; araw=%s;;;; net_in=%s;;;; net_out=%s;;;; connections=%s;;;;" \
      % (insert,
         query,
         update,
         delete,
         getmore,
         command,
         flushes,
         mapped,
         vsize,
         res,
         faults,
         locked,
         miss,
         qrqw,
         araw,
         net_in,
         net_out,
         connections)
