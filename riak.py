#!/usr/bin/env python
import sys
import requests

URL = 'http://localhost:8098/stats'
try:
    resp = requests.get(URL, timeout=60).json()
except:
    print "Plugin Failed! Unable to connect to %s" % URL
    sys.exit(2)

exclude_list = ['goldrush_version', 'erlang_js_version', 'riak_kv_version', 'riak_pipe_version', 'compiler_version',
                'sys_smp_support', 'cluster_info_version', 'webmachine_version', 'ring_ownership', 'sys_threads_enabled',
                'basho_stats_version', 'stdlib_version', 'bitcask_version', 'riak_core_version', 'sys_driver_version',
                'sys_otp_release', 'riak_control_version', 'ring_members', 'runtime_tools_version', 'lager_version',
                'sys_system_version', 'connected_nodes', 'public_key_version', 'riak_search_version', 'os_mon_version',
                'crypto_version', 'syntax_tools_version', 'riak_api_version', 'nodename', 'merge_index_version',
                'inets_version', 'sys_system_architecture', 'ssl_version', 'mochiweb_version', 'storage_backend',
                'sys_logical_processors']
                
result = "OK | "
for k, v in resp.iteritems():
    if k not in exclude_list:
        result += str(k) + '=' + str(v) + ';;;; '

print result
sys.exit(0)
