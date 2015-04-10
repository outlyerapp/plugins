#!/usr/bin/env python
import sys
import wmi 

c = wmi.WMI () 
process_info = {} 

for process in c.Win32_Process(): 
    id = process.ProcessID
    for p in c.Win32_PerfFormattedData_PerfProc_Process(IDProcess=id):
        name = p.Name.replace('.', '_').lower()
        process_info[name + '.elapsed_time'] = p.ElapsedTime
    	process_info[name + '.handle_count'] = p.HandleCount
    	process_info[name + '.io_data_bytes_per_sec'] = p.IODataBytesPersec
    	process_info[name + '.io_data_ops_per_sec'] = p.IODataOperationsPersec
    	process_info[name + '.io_other_bytes_per_sec'] = p.IOOtherBytesPersec
    	process_info[name + '.io_other_ops_per_sec'] = p.IOOtherOperationsPersec
    	process_info[name + '.io_read_bytes_per_sec'] = p.IOReadBytesPersec
    	process_info[name + '.io_read_ops_per_sec'] = p.IOReadOperationsPersec
    	process_info[name + '.io_write_bytes_per_sec'] = p.IOWriteBytesPersec
    	process_info[name + '.io_write_ops_per_sec'] = p.IOWriteOperationsPersec
    	process_info[name + '.page_faults_per_sec'] = p.PageFaultsPersec
    	process_info[name + '.page_file_bytes'] = p.PageFileBytes
    	process_info[name + '.page_file_bytes_peak'] = p.PageFileBytesPeak
    	process_info[name + '.percent_priv_time'] = p.PercentPrivilegedTime
    	process_info[name + '.percent_proc_time'] = p.PercentProcessorTime
    	process_info[name + '.percent_user_time'] = p.PercentUserTime
    	process_info[name + '.pool_non_paged_bytes'] = p.PoolNonpagedBytes
    	process_info[name + '.pool_paged_bytes'] = p.PoolPagedBytes
    	process_info[name + '.priority_base'] = p.PriorityBase
    	process_info[name + '.private_bytes'] = p.PrivateBytes
    	process_info[name + '.thread_count'] = p.ThreadCount
    	process_info[name + '.virtual_bytes'] = p.VirtualBytes
    	process_info[name + '.virtual_bytes_peak'] = p.VirtualBytesPeak
    	process_info[name + '.working_set'] = p.WorkingSet
    	process_info[name + '.working_set_peak'] = p.WorkingSetPeak
    	process_info[name + '.working_set_priv'] = p.WorkingSetPrivate

output = 'OK | '
for k, v in process_info.iteritems():
    output += k + '=' + str(v) + ';;;; '

print output
sys.exit(2)

