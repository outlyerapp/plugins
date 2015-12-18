#!/usr/bin/env python
import os
import re
import subprocess
import sys

'''This plugin requires netstat. On Ubuntu run apt-get install net-tools'''

port = '22'

############################################
cmd = "/bin/netstat -tn| grep ESTABLISHED "
try:
    resp = subprocess.check_output(cmd, stderr=subprocess.PIPE,shell=True)
    
except:
    print "netstat execution failure, install net-tools package"
    sys.exit(2)

connections_est = resp.split('\n')
i = 0
o = 0
for connection in connections_est:
    if connection:
        local_side = connection.split()[3]
        local_port = local_side.split(':')[1]
        if local_port == '22':
            i=i+1
        #print 'input %d '% i
        remote_side = connection.split()[4]
        remote_port = remote_side.split(':')[1]
        if remote_port == '22':
            o=o+1
        #print 'output %d '% o
output = "OK | connections_in=%d;;;; connections_out=%d;;;;" % (i,o)
print output
sys.exit(0)    
