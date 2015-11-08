#!/usr/bin/env python
from threading import Thread
import subprocess
from Queue import Queue

'''
This script pings a list of addresses and returns the status and round trip stats for each
'''

addresses = ["www.google.com"]
num_threads = 4
num_pings = 5


queue = Queue()
metrics = {}


def ping(i, q):
    while True:
        address = q.get()
        cmd = "ping -c %i %s" % (num_pings, address)
        try:
            cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        except subprocess.CalledProcessError:
            metrics[address + '.status'] = 2
        else:
            address = address.replace('.', '_')
            metrics[address + '.status'] = 0
            cmd_output = filter(None, cmd_output.split('\n'))[-1].split('=')[1].replace(' ms', '')
            rtt = cmd_output.split('/')
            rtt = [x.strip(' ') for x in rtt]
            metrics[address + '.min'] = rtt[0] + 'ms'
            metrics[address + '.avg'] = rtt[1] + 'ms'
            metrics[address + '.max'] = rtt[2] + 'ms'
            metrics[address + '.stddev'] = rtt[3] + 'ms'
        q.task_done()


for i in range(num_threads):
    worker = Thread(target=ping, args=(i, queue))
    worker.setDaemon(True)
    worker.start()


for a in addresses:
    queue.put(a)

queue.join()

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output