import os
import re
import subprocess
import sys
import time
import json
from datetime import datetime

MYSQL_USER = ''
MYSQL_PASSWORD = ''

no_rates = ['Binlog_snapshot_file', 'Binlog_snapshot_position', 'Binlog_cache_disk_use', 'Binlog_cache_use', 'Binlog_stmt_cache_disk_use',
           'Binlog_stmt_cache_use', 'Compression', 'Innodb_buffer_pool_dump_status', 'Innodb_buffer_pool_load_status', 
           'Innodb_buffer_pool_pages_data','Innodb_buffer_pool_bytes_data', 'Innodb_buffer_pool_pages_dirty', 'Innodb_buffer_pool_bytes_dirty', 
           'Innodb_buffer_pool_pages_free', 'Innodb_buffer_pool_pages_misc', 'Innodb_buffer_pool_pages_old', 'Innodb_buffer_pool_pages_total', 
           'Innodb_buffer_pool_wait_free','Innodb_checkpoint_age', 'Innodb_checkpoint_max_age', 'Innodb_have_atomic_builtins', 
           'Innodb_history_list_length','Innodb_ibuf_free_list', 'Innodb_ibuf_segment_size', 'Innodb_ibuf_size', 'Innodb_lsn_current', 
           'Innodb_lsn_flushed', 'Innodb_lsn_last_checkpoint', 'Innodb_master_thread_active_loops', 'Innodb_master_thread_idle_loops', 
           'Innodb_max_trx_id','Innodb_mem_adaptive_hash', 'Innodb_mem_dictionary', 'Innodb_mem_total', 'Innodb_oldest_view_low_limit_trx_id', 
           'Innodb_page_size','Innodb_purge_trx_id', 'Innodb_purge_undo_no', 'Innodb_row_lock_time', 'Innodb_row_lock_time_avg', 
           'Innodb_row_lock_time_max','Innodb_num_open_files', 'Innodb_read_views_memory', 'Innodb_descriptors_memory', 'Innodb_available_undo_logs', 
           'Key_blocks_not_flushed','Key_blocks_unused', 'Key_blocks_used', 'Last_query_cost', 'Last_query_partial_plans', 'Max_statement_time_exceeded',
           'Max_statement_time_set', 'Max_statement_time_set_failed', 'Max_used_connections', 'Not_flushed_delayed_rows', 'Open_files','Open_streams', 
           'Open_table_definitions', 'Open_tables', 'Opened_files', 'Opened_table_definitions', 'Opened_tables', 'Prepared_stmt_count', 
           'Qcache_free_blocks', 'Qcache_free_memory', 'Qcache_not_cached', 'Qcache_queries_in_cache', 'Qcache_total_blocks', 'Rsa_public_key', 
           'Slave_heartbeat_period', 'Slave_last_heartbeat', 'Slave_open_temp_tables', 'Slave_received_heartbeats','Slave_running', 'Slow_launch_threads', 
           'Ssl_cipher', 'Ssl_cipher_list', 'Ssl_client_connects', 'Ssl_ctx_verify_depth', 'Ssl_ctx_verify_mode','Ssl_default_timeout', 
           'Ssl_server_not_after', 'Ssl_server_not_before', 'Ssl_session_cache_mode', 'Ssl_session_cache_size', 'Ssl_used_session_cache_entries',
           'Ssl_verify_depth', 'Ssl_verify_mode', 'Ssl_version', 'Tc_log_max_pages_used', 'Tc_log_page_size', 'Threadpool_idle_threads',
           'Threadpool_threads', 'Threads_cached', 'Threads_connected', 'Threads_running', 'Uptime', 'Uptime_since_flush_status']

TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'dl-mysql_status_v2.json'
TIMESTAMP = datetime.now().strftime('%s')
status = {}

def get_mysql_status():
    command = ['/usr/bin/mysql', '-s', '-N', '-s', '-e', 'show global status']
    if MYSQL_USER:
        command.append('-u%s' % MYSQL_USER)
    if MYSQL_PASSWORD:
        command.append('-p%s' % MYSQL_PASSWORD)
    
    try:
        resp = subprocess.check_output(command)
    except:
        print "connection failure"
        sys.exit(2)
    
    metric_list = resp.split('\n')
    metric_list.sort()
    for line in metric_list:
        if line:
            metric = line.split('\t')
            k =  metric[0].strip().lower()
            k = k.replace('com_', '',1)
            v = metric[1]
            status[k] = v
    return status

### Rate Calculation
def tmp_file():
    # Ensure the dataloop tmp dir is available
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)

def get_cache():
    with open(TMPDIR + '/' + TMPFILE, 'r') as json_fp:
        try:
            json_data = json.load(json_fp)
        except:
            print "not a valid json file. rates calculations impossible"
            json_data = []
    return json_data

def write_cache(cache):
    with open(TMPDIR + '/' + TMPFILE, 'w') as json_fp:
        try:
            json.dump(cache, json_fp)
        except:
            print "unable to write cache file, future rates will be hard to calculate"

def cleanse_cache(cache):
    try:
        # keep the cache at a max of 1 hour of data
        while (int(TIMESTAMP) - int(cache[0]['timestamp'])) >= 3600:
            cache.pop(0)
        # keep the cache list to 120
        while len(cache) >= 120:
            cache.pop(0)
        return cache
    except:
        os.remove(TMPDIR + '/' + TMPFILE)

def calculate_rates(data_now, json_data, rateme):
    # Assume last value gives up to an hour's worth of stats
    # ie 120 values stored every 30 secs
    # pop the first value off our cache and caluculate the rate over the timeperiod
    if len(json_data) > 1:
        try:
            history = json_data[0]
            seconds_diff = int(TIMESTAMP) - int(history['timestamp'])
            rate_diff = float(data_now[rateme]) - float(history[rateme])
            data_per_second = "{0:.2f}".format(rate_diff / seconds_diff)
            return data_per_second
        except:
            return None


### Main program

# Ensure the tmp dir and file exist
tmp_file()

# Get our cache of data
json_data = get_cache()
#print json_data
if len(json_data) > 0:
    json_data = cleanse_cache(json_data)

# get the current ngin status
result = get_mysql_status()

all_rates = list(result.keys())
rates = list(set(all_rates) - set(no_rates))

for rate in rates:
    _ = calculate_rates(result, json_data, rate)
    if _ is not None:
        result[rate + "_per_sec"] = _


# append to the cache and write out for the next pass
dated_result = result
dated_result['timestamp'] = TIMESTAMP
json_data.append(dated_result)
write_cache(json_data)

# Finally nagios exit with perfdata
perf_data = "OK | "
for k, v in result.iteritems():
    perf_data += "%s=%s;;;; " % (k, v)
print perf_data
sys.exit(0)
