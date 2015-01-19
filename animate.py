#!/usr/bin/python

# import stuff
import sys
from serial import Serial
from time import sleep, time

# helper: coerce integer
def coerceInt( value, low, high ): return max( low, min( high, int(value) ) )

# parse required argument: automation
if len(sys.argv) >= 2:
    preset = sys.argv[1]
else:
    print
    print "Usage:", sys.argv[0], " AUTOMATION [4CH-MASK] [SPEED]"
    print
    print "AUTOMATION  pulse | sweep | peews | static"
    print "4CH-MASK    0..255,0..255,0..255,0..255"
    print "SPEED       1..1000"
    print
    print "Example:", sys.argv[0], "pulse", "255,255,255,255", "10"
    print
    exit(1)

# define maximum speed
maxSpeed = 1000

# parse colour expression (default: 255,255,255,255)
colourCSV = sys.argv[2].strip() if len(sys.argv) >= 3 else "255,255,255,255"
colour = colourCSV.split(',')

# parse speed argument (default: 10)
try:              speed = int(sys.argv[3])
except Exception: speed = 10
if speed < 1:        speed = 1
if speed > maxSpeed: speed = maxSpeed

# sanitize colour values (0..255 integers)
colour = [ coerceInt( int(col), 0, 255 ) for col in colour ]

# desired duration of send [s] (20 ms = 50 fps)
try:              sendDuration = float(sys.argv[4])
except Exception: sendDuration = 0.02

# number of quad-channels to output (i.e. number of 4-channel devices)
activeQuadChannels = 16

# serial device settings
device = '/dev/ttyACM0'
baud   = 115200



# helper: calculate 4-channel-value from mask and factor (linear scaling)
def quadValueFromFactor( factor ): return [ int(round( col * float(factor)/maxSpeed )) for col in colour ]

# pulse
def pulse():
    factor = 0
    step   = speed
    while True:
        factor += step
        if factor < 0 or factor > maxSpeed:
            step *= -1
            factor = coerceInt( factor, 0, maxSpeed )
        send( quadValueFromFactor( factor ) * activeQuadChannels )
        
# sweep
def sweep():
    factor = 0
    while True:
        factor += speed
        if factor > maxSpeed: factor = 0
        send( quadValueFromFactor( factor ) * activeQuadChannels )

# sweep inversed
def peews():
    factor = maxSpeed
    while True:
        factor -= speed
        if factor < 0: factor = maxSpeed
        send( quadValueFromFactor( factor ) * activeQuadChannels )

# static
def static():
    while True:
        send( quadValueFromFactor( maxSpeed ) * activeQuadChannels )



# send channels
def send( channels ):
    
    # take time
    start = time()
    
    # make byte string
    data = ''
    for decimal in channels: data += chr(int(decimal))
    
    # send to device and wait for response
    serial.write( data )
    status = serial.readline()

    # calculate waiting time
    remaining = sendDuration - ( time()-start )
    if remaining < 0: remaining = 0
    
    # wait
    sleep( remaining )
    
    # calculate current frame rate and load
    frameRate = 1 / ( time()-start )
    load = 1 - float(remaining) / sendDuration
    
    # calculate sliding averages
    send.frameRateHistory += [ frameRate ]
    send.loadHistory      += [ load ]
    frameRate = sum(send.frameRateHistory) / len(send.frameRateHistory)
    load      = sum(send.loadHistory)      / len(send.loadHistory)
    
    # pop first elements to coerceInt size (FIFO)
    send.frameRateHistory.pop(0)
    send.loadHistory.pop(0)
    
    # log
    print "\r",
    print "Load: %3d %%" % int(load*100), "|", "Rate: %4.1f fps" % frameRate, "|", status.strip(),

# value histories in send() (for sliding averages)
send.frameRateHistory = [0] * 10
send.loadHistory      = [0] * 10



# helper: neat mode announcement
def printMode(mode): print mode, "on", "4x"+str(activeQuadChannels), "channels with speed", speed, "and mask", colourCSV

# open device and run
with Serial( device, baud, bytesize=8, parity='N', timeout=1 ) as serial:
    
    try:
        
        if preset == 'pulse':
            printMode("Pulse")
            pulse()
        
        if preset == 'sweep':
            printMode("Sweep")
            sweep()
        
        if preset == 'peews':
            printMode("Sweep inversed")
            peews()
            
        if preset == 'static':
            printMode("Static")
            static()
            
    
    # quit with Ctrl+C
    except KeyboardInterrupt:
        exit(0)
        
    # any other exceptions
    except Exception as error:
        raise error
        exit(1)
