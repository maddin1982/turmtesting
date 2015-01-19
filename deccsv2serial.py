#!/usr/bin/python

'''
A minimal script for writing binary data to serial devices.

- takes comma-separated decimal values on stdin (terminate lines with \n),
  converts them to bytes and writes them to the serial device
- responses from the device are dumped to stdout
- runs infinitely until receiving the string "quit" instead of a CSV line

nick@bitfasching.de
01/2015
'''

import sys
from serial import Serial

# parse arguments
if len(sys.argv) >= 3:
    (  device, baud ) = ( sys.argv[1], sys.argv[2] )
else:
    print "Usage:", sys.argv[0], " DEVICE BAUD"
    exit(1)

# open device
with Serial( device, baud, bytesize=8, parity='N', timeout=1 ) as serial:

    while True:
        
        # read next line from stdin
        csv = sys.stdin.readline().strip()
        
        # check if input is a command to quit
        if csv == "quit": break
        
        # get list from csv
        decimals = csv.split( ',' )
        
        # make binary string
        data = ''
        for decimal in decimals: data += chr(int(decimal))
        
        # send to device
        serial.write( data )
        
        # read status
        status = serial.readline().strip()
        
        # print status to stdout and flush
        sys.stdout.write( status + "\n" );
        sys.stdout.flush();
