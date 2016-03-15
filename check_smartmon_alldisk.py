#!/usr/bin/env python2.7

"""
__author__ = Garfield Carneiro
Running script in debug mode
[gary@myserver ~]$ ./check_smartmon_cmd.py  --debug
Mon Mar 14 20:37:06 2016 Valid Disks are ['/dev/sdl', '/dev/sdj', '/dev/sdk', '/dev/sdh', '/dev/sdi', '/dev/sdf', '/dev/sdg', '/dev/sdd', '/dev/sde', '/dev/sdb', '/dev/sdc', '/dev/sda']
Mon Mar 14 20:37:06 2016 Checking /dev/sdl
Mon Mar 14 20:37:07 2016 Result of [/usr/bin/sudo /usr/sbin/smartctl -Hc /dev/sdl] : [SMART overall-health self-assessment test result: PASSED]
Mon Mar 14 20:37:07 2016 Disk /dev/sdl is fine
Mon Mar 14 20:37:07 2016 Checking /dev/sdj
Mon Mar 14 20:40:55 2016 Result of [/usr/bin/sudo /usr/sbin/smartctl -Hc /dev/sdj] : [SMART overall-health self-assessment test result: FAILED!]
Mon Mar 14 20:40:55 2016 /dev/sdj is having issues

CRITICAL.Disks that are having issues : ['/dev/sdj']


"""


import psutil
import commands
import argparse
import datetime
import re


def dprint(msg):
  """Print only when debugging is enabled"""
  if argv.debugflag:
    format = "%a %b %d %H:%M:%S %Y"
    today = datetime.datetime.today()
    timestamp = today.strftime(format)
    print str(timestamp + " " + msg)

parser = argparse.ArgumentParser()
parser.add_argument("--debug", "-d", dest="debugflag", default=False, action="store_true", help="Debug flag")
argv = parser.parse_args()

# Regex for Valid Device Names
reValidDeviceName = '/dev/[hsv]da*'

validPartitions = []

problemDisks = []

for partition in psutil.disk_partitions():
  if re.search(reValidDeviceName, partition.device):
    """Smartctl works only on disks not partitions. Hence we strip the number. """
    validPartitions.append(partition.device.strip(partition.device[-1]))


# Deduplicating valid partitions since different partitions get appended to 

validDisks = list(set(validPartitions))
dprint("Valid Disks are %s" % (validDisks))


"""
It might be possible that the disks are mirrored and do not match psutils.disk_partitions() 
Another reason is we have the validDeviceName regex (called reValidDeviceName ) which does not match.
The best option simply is to exit with a Status code 0 instead of creating Nagios Noise.

"""

if len(validDisks) == 0:
  print "Cant find valid disks. Exiting."
  exit(0)

for disk in validDisks:
  smartcmd = "/usr/bin/sudo /usr/sbin/smartctl -Hc %s | /bin/grep -i Health" % (disk)
  dprint("Checking %s" % (disk))
  result = commands.getstatusoutput(smartcmd)
  dprint("Result of [/usr/bin/sudo /usr/sbin/smartctl -Hc %s] : [%s]" % (disk, str(result[1])))
  
# result[0] stores status code; result[1] stores command output
  if  ("PASSED" in result[1]) or ("OK" in result[1]):
    dprint("Disk %s is fine." % (disk))
  else:
    dprint("%s is having issues." % (disk))
    problemDisks.append(disk)
    
# Deduplicating problematic partitions
problemDisks = list(set(problemDisks))

if len(problemDisks) == 0:
  print "OK. All disks are fine."
  exit(0)
elif len(problemDisks) > 0:
  print "CRITICAL.Disks that are having issues : %s" % (problemDisks)
  exit(2)
