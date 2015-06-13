#!/usr/bin/env python
import sys
import subprocess

try:
    output = subprocess.check_output(('redis-cli', 'info'))
except:
    print "Plugin Failed!"
    sys.exit(2)

metrics = output.split()
exclusion_list = ['redis_version',
                  'redis_git_sha1',
                  'redis_build_id',
                  'redis_mode',
                  'os',
                  'arch_bits',
                  'multiplexing_api',
                  'gcc_version',
                  'run_id',
                  'tcp_port',
                  'config_file',
                  'mem_allocator',
                  'rdb_last_bgsave_status',
                  'of_last_write_status',
                  'aof_last_bgrewrite_status',
                  'role'
                  ]

perf_data = "OK | "
for m in metrics:
    if ":" in m:
        k = m.split(':')[0]
        v = m.split(':')[1]
        if k not in exclusion_list:
            perf_data += "%s=%s;;;; " % (k, v)


print perf_data
sys.exit(0)