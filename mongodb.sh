#!/bin/bash

output=$(mongostat -n 1 --noheaders | tail -1)
insert=$(echo $output | awk '{ print $1}')
query=$(echo $output | awk '{ print $2}')
update=$(echo $output | awk '{ print $3}')
delete=$(echo $output | awk '{ print $4}')
getmore=$(echo $output | awk '{ print $5}')
command=$(echo $output | awk '{ print $6}')
flushes=$(echo $output | awk '{ print $7}')
mapped=$(echo $output | awk '{ print $8}')
vsize=$(echo $output | awk '{ print $9}')
res=$(echo $output | awk '{ print $10}')
faults=$(echo $output | awk '{ print $11}')
locked=$(echo $output | awk '{ print $12}')
miss=$(echo $output | awk '{ print $13}')
net_in=$(echo $output | awk '{ print $16}')
net_out=$(echo $output | awk '{ print $17}')
connections=$(echo $output | awk '{ print $18}')

echo "OK | insert=$insert;;;; query=$query;;;; update=$update;;;; delete=$delete;;;; getmore=$getmore;;;; command=$command;;;; flushes=$flushes;;;; mapped=$mapped;;;; vsize=$vsize;;;; res=$res;;;; faults=$faults;;;; locked=$locked;;;; miss=$miss;;;; net_in=$net_in;;;; net_out=$net_out;;;; connections=$connections;;;;"

