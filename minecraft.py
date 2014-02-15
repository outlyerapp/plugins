#!/usr/bin/env python

from datetime import datetime, timedelta
import sys
import string
import socket
import time
import argparse

# Exit statuses recognized by Nagios.
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# Output formatting string.
OUTPUT_OK = "MINECRAFT OK: {0} - {1} bytes in {2:.3} second response time|time={2}s;{3};{4};0.0;{5}"
OUTPUT_WARNING = "MINECRAFT WARNING: {0} - {1} bytes in {2:.3} second response time|time={2}s;{3};{4};0.0;{5}"
OUTPUT_CRITICAL = "MINECRAFT CRITICAL: {0} - {1} bytes in {2:.3} second response time|time={2}s;{3};{4};0.0;{5}"
OUTPUT_EXCEPTION = "MINECRAFT CRITICAL: {0}"
OUTPUT_UNKNOWN = "MINECRAFT UNKNOWN: Invalid arguments"

# Minecraft packet ID:s, delimiters and encoding.
MC_SERVER_LIST_PING = "\xfe"
MC_DISCONNECT = "\xff"
MC_DELIMITER = u"\xa7"
MC_ENCODING = "utf-16be"


def log(start, message):
    print("{0}: {1}".format(datetime.now() - start, message))


def get_server_info(host, port, num_checks, timeout, verbose):
    start_time = datetime.now()
    total_delta = timedelta()
    byte_count = len(MC_SERVER_LIST_PING) * num_checks

    # Contact the server multiple times to get a stable average response time.
    for i in range(0, num_checks):
        if verbose:
            iteration = "Iteration {0}/{1}: ".format(i + 1, num_checks)

        # Save start time and connect to server.
        if verbose:
            log(start_time, "{0}Connecting to {1} on port {2}.".format(iteration, host, port))
        net_start_time = datetime.now()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))

        # Send Minecraft Server List Ping packet.
        if verbose:
            log(start_time, "{0}Sending Server List Ping.".format(iteration))
        s.send(MC_SERVER_LIST_PING)

        # Receive answer from server. The largest answer returned by the server that also works with the Minecraft client
        # seems to be around 520 bytes (259 unicode character at 2 bytes each plus one start byte and one length byte).
        if verbose:
            log(start_time, "{0}Receiving data...".format(iteration))
        data = s.recv(550)
        data_len = len(data)
        byte_count += data_len
        if verbose:
            log(start_time, "{0}Received {1} bytes".format(iteration, data_len))

        s.close()

        # Check if returned data seems valid. If not, throw AssertionError exception.
        if verbose:
            if data[0] == MC_DISCONNECT:
                log(start_time, "Returned data seems valid.")
            else:
                log(start_time, "Returned data is invalid. First byte is {0:#x}.".format(ord(data[0])))

        assert data[0] == MC_DISCONNECT

        # Save response time for later average calculation.
        delta = datetime.now() - net_start_time
        total_delta += delta

        time.sleep(0.1)

    # Calculate the average response time in seconds
    total_response = total_delta.seconds + total_delta.microseconds / 1000000.0
    average_response = total_response / num_checks

    # Decode and split returned skipping the first two bytes.
    info = data[3:].decode(MC_ENCODING).split(MC_DELIMITER)

    return {'motd': info[0],
            'players': int(info[1]),
            'max_players': int(info[2]),
            'byte_count': byte_count,
            'response_time': average_response}


def main():
    parser = argparse.ArgumentParser(description="This plugin will try to connect to a Minecraft server.")

    parser.add_argument('-H', '--hostname', dest='hostname', metavar='ADDRESS', required=True,
                        help="host name or IP address")
    parser.add_argument('-p', '--port', dest='port', type=int, default=25565, metavar='INTEGER',
                        help="port number (default: 25565)")
    parser.add_argument('-n', '--number-of-checks', dest='num_checks', type=int, default=5, metavar='INTEGER',
                        help="number of checks to get stable average response time (default: 5)")
    parser.add_argument('-m', '--motd', dest='motd', default='A Minecraft Server', metavar='STRING',
                        help="expected motd in server response (default: A Minecraft Server)")
    parser.add_argument('-f', '--warn-on-full', dest='full', action='store_true',
                        help="generate warning if server is full")
    parser.add_argument('-w', '--warning', dest='warning', type=float, default=0.0, metavar='DOUBLE',
                        help="response time to result in warning status (seconds)")
    parser.add_argument('-c', '--critical', dest='critical', type=float, default=0.0, metavar='DOUBLE',
                        help="response time to result in critical status (seconds)")
    parser.add_argument('-t', '--timeout', dest='timeout', type=float, default=10.0, metavar='DOUBLE',
                        help="seconds before connection times out (default: 10)")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="show details for command-line debugging (Nagios may truncate output)")

    # Parse the arguments. If it fails, exit overriding exit code.
    try:
        args = parser.parse_args()
    except SystemExit:
        print(OUTPUT_UNKNOWN)
        sys.exit(STATE_UNKNOWN)

    try:
        info = get_server_info(args.hostname, args.port, args.num_checks, args.timeout, args.verbose)

        if string.find(info['motd'], args.motd) > -1:
            # Check if response time is above critical level.
            if args.critical and info['response_time'] > args.critical:
                print(OUTPUT_CRITICAL.format("{0} second response time".format(info['response_time']),
                                             info['byte_count'], info['response_time'], args.warning, args.critical, args.timeout))
                sys.exit(STATE_CRITICAL)

            # Check if response time is above warning level.
            if args.warning and info['response_time'] > args.warning:
                print(OUTPUT_WARNING.format("{0} second response time".format(info['response_time']),
                                            info['byte_count'], info['response_time'], args.warning, args.critical, args.timeout))
                sys.exit(STATE_WARNING)

            # Check if server is full.
            if args.full and info['players'] == info['max_players']:
                print(OUTPUT_WARNING.format("Server full! {0} players online".format(info['players']),
                                            info['byte_count'], info['response_time'], args.warning, args.critical, args.timeout))
                sys.exit(STATE_WARNING)

            print(OUTPUT_OK.format("{0}/{1} players online".format(info['players'], info['max_players']),
                                   info['byte_count'], info['response_time'], args.warning, args.critical, args.timeout))
            sys.exit(STATE_OK)

        else:
            print(OUTPUT_WARNING.format("Unexpected MOTD, {0}".format(info['motd']),
                                        info['byte_count'], info['response_time'], args.warning, args.critical, args.timeout))
            sys.exit(STATE_WARNING)

    except socket.error, msg:
        print(OUTPUT_EXCEPTION.format(msg))
        sys.exit(STATE_CRITICAL)

    except AssertionError:
        print(OUTPUT_EXCEPTION.format("Invalid data returned by server"))
        sys.exit(STATE_CRITICAL)

    except UnicodeDecodeError:
        print(OUTPUT_EXCEPTION.format("Unable to decode server response"))
        sys.exit(STATE_CRITICAL)

main()
