#!/bin/sh
PATH=/usr/bin:/sbin:/bin

zfs_pool="tank" # Pool to check
interval="1" # zpool iostat interval in seconds. Suggested value is 60.

if ! [ -n "$(pgrep -f "zfs.zpool.iostat.write.bandwidth")" ]; then
sudo zpool iostat $zfs_pool $interval | stdbuf -o0 awk 'NR > 3 {print($7)}' | stdbuf -o0 sed -e 's/K/\*1024/g' -e 's/M/\*1048576/g' -e 's/G/\*1073741824/g' | bc | stdbuf -o0 awk '{printf("%d\n",$1 + 0.5)}' &
fi

if ! [ -n "$(pgrep -f "zfs.zpool.iostat.read.bandwidth")" ]; then
sudo zpool iostat $zfs_pool $interval | stdbuf -o0 awk 'NR > 3 {print($6)}' | stdbuf -o0 sed -e 's/K/\*1024/g' -e 's/M/\*1048576/g' -e 's/G/\*1073741824/g' | bc | stdbuf -o0 awk '{printf("%d\n",$1 + 0.5)}' &
fi

if ! [ -n "$(pgrep -f "zfs.zpool.iostat.write.ops")" ]; then
sudo zpool iostat $zfs_pool $interval | stdbuf -o0 awk 'NR > 3 {print($5)}' | stdbuf -o0 sed -e 's/K/\*1024/g' -e 's/M/\*1048576/g' -e 's/G/\*1073741824/g' | bc | stdbuf -o0 awk '{printf("%d\n",$1 + 0.5)}' &
fi

if ! [ -n "$(pgrep -f "zfs.zpool.iostat.read.ops")" ]; then
sudo zpool iostat $zfs_pool $interval | stdbuf -o0 awk 'NR > 3 {print($4)}' | stdbuf -o0 sed -e 's/K/\*1024/g' -e 's/M/\*1048576/g' -e 's/G/\*1073741824/g' | bc | stdbuf -o0 awk '{printf("%d\n",$1 + 0.5)}' &
fi