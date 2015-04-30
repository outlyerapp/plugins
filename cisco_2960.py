#!/usr/bin/env python
from pysnmp.entity.rfc3413.oneliner import cmdgen
import sys

IP = ''
PORT = 161
COMMUNITY = ''
metrics = {}

oids = { '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1': 'cpmCPUTotal1minRev',
         '1.3.6.1.4.1.9.9.109.1.1.1.1.8.1': 'cpmCPUTotal5minRev',
         '1.3.6.1.4.1.9.9.48.1.1.1.5.1':    'ciscoMemoryPoolUsed_processor',
         '1.3.6.1.4.1.9.9.48.1.1.1.5.2':    'ciscoMemoryPoolUsed_io',
         '1.3.6.1.4.1.9.9.48.1.1.1.6.1':    'ciscoMemoryPoolFree_processor',
         '1.3.6.1.4.1.9.9.48.1.1.1.6.2':    'ciscoMemoryPoolFree_io',
         '1.3.6.1.4.1.9.3.6.6.0':           'processorRam',
         '1.3.6.1.4.1.9.3.6.7.0':           'nvRAMSize',
         '1.3.6.1.4.1.9.3.6.8.0':           'nvRAMUsed',	
         '1.3.6.1.4.1.9.2.2.1.1.1.5003':  'EtherChannel',
         '1.3.6.1.4.1.9.2.2.1.1.1.10101': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10102': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10103': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10104': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10105': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10106': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10107': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10108': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10109': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10110': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10111': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10112': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10113': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10114': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10115': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10116': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10117': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10118': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10119': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10120': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10121': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10122': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10123': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.1.10124': 'Gigabit Ethernet',
         '1.3.6.1.4.1.9.2.2.1.1.6.5003':  'locIfInBitsSecPortEtherchannel',
         '1.3.6.1.4.1.9.2.2.1.1.6.10101': 'locIfInBitsSecPort01',
         '1.3.6.1.4.1.9.2.2.1.1.6.10102': 'locIfInBitsSecPort02',
         '1.3.6.1.4.1.9.2.2.1.1.6.10103': 'locIfInBitsSecPort03',
         '1.3.6.1.4.1.9.2.2.1.1.6.10104': 'locIfInBitsSecPort04',
         '1.3.6.1.4.1.9.2.2.1.1.6.10105': 'locIfInBitsSecPort05',
         '1.3.6.1.4.1.9.2.2.1.1.6.10106': 'locIfInBitsSecPort06',
         '1.3.6.1.4.1.9.2.2.1.1.6.10107': 'locIfInBitsSecPort07',
         '1.3.6.1.4.1.9.2.2.1.1.6.10108': 'locIfInBitsSecPort08',
         '1.3.6.1.4.1.9.2.2.1.1.6.10109': 'locIfInBitsSecPort09',
         '1.3.6.1.4.1.9.2.2.1.1.6.10110': 'locIfInBitsSecPort10',
         '1.3.6.1.4.1.9.2.2.1.1.6.10111': 'locIfInBitsSecPort11',
         '1.3.6.1.4.1.9.2.2.1.1.6.10112': 'locIfInBitsSecPort12',
         '1.3.6.1.4.1.9.2.2.1.1.6.10113': 'locIfInBitsSecPort13',
         '1.3.6.1.4.1.9.2.2.1.1.6.10114': 'locIfInBitsSecPort14',
         '1.3.6.1.4.1.9.2.2.1.1.6.10115': 'locIfInBitsSecPort15',
         '1.3.6.1.4.1.9.2.2.1.1.6.10116': 'locIfInBitsSecPort16',
         '1.3.6.1.4.1.9.2.2.1.1.6.10117': 'locIfInBitsSecPort17',
         '1.3.6.1.4.1.9.2.2.1.1.6.10118': 'locIfInBitsSecPort18',
         '1.3.6.1.4.1.9.2.2.1.1.6.10119': 'locIfInBitsSecPort19',
         '1.3.6.1.4.1.9.2.2.1.1.6.10120': 'locIfInBitsSecPort20',
         '1.3.6.1.4.1.9.2.2.1.1.6.10121': 'locIfInBitsSecPort21',
         '1.3.6.1.4.1.9.2.2.1.1.6.10122': 'locIfInBitsSecPort22',
         '1.3.6.1.4.1.9.2.2.1.1.6.10123': 'locIfInBitsSecPort23',
         '1.3.6.1.4.1.9.2.2.1.1.6.10124': 'locIfInBitsSecPort24',
         '1.3.6.1.4.1.9.2.2.1.1.6.5003':  'locIfInBitsSecPortEtherchannel',
         '1.3.6.1.4.1.9.2.2.1.1.7.10101': 'locIfInPktsSecPort01',
         '1.3.6.1.4.1.9.2.2.1.1.7.10102': 'locIfInPktsSecPort02',
         '1.3.6.1.4.1.9.2.2.1.1.7.10103': 'locIfInPktsSecPort03',
         '1.3.6.1.4.1.9.2.2.1.1.7.10104': 'locIfInPktsSecPort04',
         '1.3.6.1.4.1.9.2.2.1.1.7.10105': 'locIfInPktsSecPort05',
         '1.3.6.1.4.1.9.2.2.1.1.7.10106': 'locIfInPktsSecPort06',
         '1.3.6.1.4.1.9.2.2.1.1.7.10107': 'locIfInPktsSecPort07',
         '1.3.6.1.4.1.9.2.2.1.1.7.10108': 'locIfInPktsSecPort08',
         '1.3.6.1.4.1.9.2.2.1.1.7.10109': 'locIfInPktsSecPort09',
         '1.3.6.1.4.1.9.2.2.1.1.7.10110': 'locIfInPktsSecPort10',
         '1.3.6.1.4.1.9.2.2.1.1.7.10111': 'locIfInPktsSecPort11',
         '1.3.6.1.4.1.9.2.2.1.1.7.10112': 'locIfInPktsSecPort12',
         '1.3.6.1.4.1.9.2.2.1.1.7.10113': 'locIfInPktsSecPort13',
         '1.3.6.1.4.1.9.2.2.1.1.7.10114': 'locIfInPktsSecPort14',
         '1.3.6.1.4.1.9.2.2.1.1.7.10115': 'locIfInPktsSecPort15',
         '1.3.6.1.4.1.9.2.2.1.1.7.10116': 'locIfInPktsSecPort16',
         '1.3.6.1.4.1.9.2.2.1.1.7.10117': 'locIfInPktsSecPort17',
         '1.3.6.1.4.1.9.2.2.1.1.7.10118': 'locIfInPktsSecPort18',
         '1.3.6.1.4.1.9.2.2.1.1.7.10119': 'locIfInPktsSecPort19',
         '1.3.6.1.4.1.9.2.2.1.1.7.10120': 'locIfInPktsSecPort20',
         '1.3.6.1.4.1.9.2.2.1.1.7.10121': 'locIfInPktsSecPort21',
         '1.3.6.1.4.1.9.2.2.1.1.7.10122': 'locIfInPktsSecPort22',
         '1.3.6.1.4.1.9.2.2.1.1.7.10123': 'locIfInPktsSecPort23',
         '1.3.6.1.4.1.9.2.2.1.1.7.10124': 'locIfInPktsSecPort24',
         '1.3.6.1.4.1.9.2.2.1.1.8.5003':  'locIfOutBitsSecPortEtherchannel',
         '1.3.6.1.4.1.9.2.2.1.1.8.10101': 'locIfOutBitsSecPort01',
         '1.3.6.1.4.1.9.2.2.1.1.8.10102': 'locIfOutBitsSecPort02',
         '1.3.6.1.4.1.9.2.2.1.1.8.10103': 'locIfOutBitsSecPort03',
         '1.3.6.1.4.1.9.2.2.1.1.8.10104': 'locIfOutBitsSecPort04',
         '1.3.6.1.4.1.9.2.2.1.1.8.10105': 'locIfOutBitsSecPort05',
         '1.3.6.1.4.1.9.2.2.1.1.8.10106': 'locIfOutBitsSecPort06',
         '1.3.6.1.4.1.9.2.2.1.1.8.10107': 'locIfOutBitsSecPort07',
         '1.3.6.1.4.1.9.2.2.1.1.8.10108': 'locIfOutBitsSecPort08',
         '1.3.6.1.4.1.9.2.2.1.1.8.10109': 'locIfOutBitsSecPort09',
         '1.3.6.1.4.1.9.2.2.1.1.8.10110': 'locIfOutBitsSecPort10',
         '1.3.6.1.4.1.9.2.2.1.1.8.10111': 'locIfOutBitsSecPort11',
         '1.3.6.1.4.1.9.2.2.1.1.8.10112': 'locIfOutBitsSecPort12',
         '1.3.6.1.4.1.9.2.2.1.1.8.10113': 'locIfOutBitsSecPort13',
         '1.3.6.1.4.1.9.2.2.1.1.8.10114': 'locIfOutBitsSecPort14',
         '1.3.6.1.4.1.9.2.2.1.1.8.10115': 'locIfOutBitsSecPort15',
         '1.3.6.1.4.1.9.2.2.1.1.8.10116': 'locIfOutBitsSecPort16',
         '1.3.6.1.4.1.9.2.2.1.1.8.10117': 'locIfOutBitsSecPort17',
         '1.3.6.1.4.1.9.2.2.1.1.8.10118': 'locIfOutBitsSecPort18',
         '1.3.6.1.4.1.9.2.2.1.1.8.10119': 'locIfOutBitsSecPort19',
         '1.3.6.1.4.1.9.2.2.1.1.8.10120': 'locIfOutBitsSecPort20',
         '1.3.6.1.4.1.9.2.2.1.1.8.10121': 'locIfOutBitsSecPort21',
         '1.3.6.1.4.1.9.2.2.1.1.8.10122': 'locIfOutBitsSecPort22',
         '1.3.6.1.4.1.9.2.2.1.1.8.10123': 'locIfOutBitsSecPort23',
         '1.3.6.1.4.1.9.2.2.1.1.8.10124': 'locIfOutBitsSecPort24',
         '1.3.6.1.4.1.9.2.2.1.1.8.5003':  'locIfOutBitsSecPortEtherchannel',
         '1.3.6.1.4.1.9.2.2.1.1.9.10101': 'locIfOutPktsSecPort01',
         '1.3.6.1.4.1.9.2.2.1.1.9.10102': 'locIfOutPktsSecPort02',
         '1.3.6.1.4.1.9.2.2.1.1.9.10103': 'locIfOutPktsSecPort03',
         '1.3.6.1.4.1.9.2.2.1.1.9.10104': 'locIfOutPktsSecPort04',
         '1.3.6.1.4.1.9.2.2.1.1.9.10105': 'locIfOutPktsSecPort05',
         '1.3.6.1.4.1.9.2.2.1.1.9.10106': 'locIfOutPktsSecPort06',
         '1.3.6.1.4.1.9.2.2.1.1.9.10107': 'locIfOutPktsSecPort07',
         '1.3.6.1.4.1.9.2.2.1.1.9.10108': 'locIfOutPktsSecPort08',
         '1.3.6.1.4.1.9.2.2.1.1.9.10109': 'locIfOutPktsSecPort09',
         '1.3.6.1.4.1.9.2.2.1.1.9.10110': 'locIfOutPktsSecPort10',
         '1.3.6.1.4.1.9.2.2.1.1.9.10111': 'locIfOutPktsSecPort11',
         '1.3.6.1.4.1.9.2.2.1.1.9.10112': 'locIfOutPktsSecPort12',
         '1.3.6.1.4.1.9.2.2.1.1.9.10113': 'locIfOutPktsSecPort13',
         '1.3.6.1.4.1.9.2.2.1.1.9.10114': 'locIfOutPktsSecPort14',
         '1.3.6.1.4.1.9.2.2.1.1.9.10115': 'locIfOutPktsSecPort15',
         '1.3.6.1.4.1.9.2.2.1.1.9.10116': 'locIfOutPktsSecPort16',
         '1.3.6.1.4.1.9.2.2.1.1.9.10117': 'locIfOutPktsSecPort17',
         '1.3.6.1.4.1.9.2.2.1.1.9.10118': 'locIfOutPktsSecPort18',
         '1.3.6.1.4.1.9.2.2.1.1.9.10119': 'locIfOutPktsSecPort19',
         '1.3.6.1.4.1.9.2.2.1.1.9.10120': 'locIfOutPktsSecPort20',
         '1.3.6.1.4.1.9.2.2.1.1.9.10121': 'locIfOutPktsSecPort21',
         '1.3.6.1.4.1.9.2.2.1.1.9.10122': 'locIfOutPktsSecPort22',
         '1.3.6.1.4.1.9.2.2.1.1.9.10123': 'locIfOutPktsSecPort23',
         '1.3.6.1.4.1.9.2.2.1.1.9.10124': 'locIfOutPktsSecPort24',
       }

# Get Specific MIBS
cmdGen = cmdgen.CommandGenerator()

errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
    cmdgen.CommunityData(COMMUNITY),
    cmdgen.UdpTransportTarget((IP, PORT)),
     # cmdgen.MibVariable('SNMPv2-MIB', 'sysDescr', 0),
    '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',
    '1.3.6.1.4.1.9.9.109.1.1.1.1.8.1',
    '1.3.6.1.4.1.9.9.48.1.1.1.5.1',
    '1.3.6.1.4.1.9.9.48.1.1.1.5.2',
    '1.3.6.1.4.1.9.9.48.1.1.1.6.1',
    '1.3.6.1.4.1.9.9.48.1.1.1.6.2',
    '1.3.6.1.4.1.9.3.6.6.0',
    '1.3.6.1.4.1.9.3.6.7.0',
    '1.3.6.1.4.1.9.3.6.8.0',
    #lookupNames=True, lookupValues=True
)

# Check for errors and print out results
if errorIndication:
    print(errorIndication)
elif errorStatus:
    print(errorStatus)
else:
    for oid, val in varBinds:
        # print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
        if str(oid) in oids.keys():
            name = oids[str(oid)]
            metrics[name] = val
        else:
            name = oid


# Walk MIBS for values
cmdGen = cmdgen.CommandGenerator()

# walking
errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
    cmdgen.CommunityData(COMMUNITY),
    cmdgen.UdpTransportTarget((IP, PORT)),
    '1.3.6.1.4.1.9.2.2.1.1.6',
    '1.3.6.1.4.1.9.2.2.1.1.7',
    '1.3.6.1.4.1.9.2.2.1.1.8',
    '1.3.6.1.4.1.9.2.2.1.1.9',
)


if errorIndication:
    print(errorIndication)
else:
    if errorStatus:
        print('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
            )
        )
    else:
        for varBindTableRow in varBindTable:
            for oid, val in varBindTableRow:
                if str(oid) in oids.keys():
                    name = oids[str(oid)]
                    metrics[name] = val
                else:
                    name = str(oid)
                #print('%s = %s' % (name, val))
        
        
message = "OK | "          
for k,v in metrics.iteritems():
    message += "%s=%s;;; " % (k,v)

print message
sys.exit(0)
