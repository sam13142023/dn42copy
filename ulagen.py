#!/usr/bin/env python

# Attribution: This script is copied and modified from one published by github user andrewlkho.
# Repository: https://github.com/andrewlkho/ulagen

import hashlib
import time
import uuid

def get_eui64():
  mac = uuid.getnode()
  eui64 = mac >> 24 << 48 | 0xfffe000000 | mac & 0xffffff
  eui64_canon = "-".join([format(eui64, "02X")[i:i+2] for i in range(0, 18, 2)])
  return eui64_canon

def time_ntpformat():
  # Seconds relative to 1900-01-01 00:00
  return time.time() - time.mktime((1900, 1, 1, 0, 0, 0, 0, 1, -1))

def main():
  h = hashlib.sha1()
  h.update(get_eui64() + str(time_ntpformat()))
  globalid = h.hexdigest()[0:10]

  prefix = ":".join(("fd" + globalid[0:2], globalid[2:6], globalid[6:10]))
  print "# /path/to/dn42/registry/" + " - " + "data/inet6num/" + prefix + "::_48" + "\n"
  print "inet6num:           " + prefix + ":0000:0000:0000:0000:0000" + " - " + prefix + ":ffff:ffff:ffff:ffff:ffff"
  print "cidr:               " + prefix + "::/48"
  print "netname:            " + "EXAMPLE-NET-1"
  print "admin-c:            " + "EXAMPLE-DN42"
  print "tech-c:             " + "EXAMPLE-DN42"
  print "mnt-by:             " + "EXAMPLE-MNT"
  print "status:             " + "ASSIGNED"
  print "source:             " + "DN42"
  print "\n# /path/to/dn42/registry/" + " - " + "data/route6/" + prefix + "::_48" + "\n"
  print "route6:             " + prefix + "::/48"
  print "origin:             " + "AS<INSERT_NUMERIC_AUT_NUM_VALUE>"
  print "max-length:         " + "48"
  print "mnt-by:             " + "EXAMPLE-MNT"
  print "source:             " + "DN42"
  print "\n" + "# Replace EXAMPLE with something else. E.g. OCEAN-{NET-1,DN42,MNT}"
  print "#"
  print "# Please remember this an examle object. It can be used as is if you replace EXAMPLE in the above lines."
  print "# To find out more about required and optional keys for the inet6num object. Please see data/schema/{INET6NUM,ROUTE6}-SCHEMA"

if __name__ == "__main__":
  main()
