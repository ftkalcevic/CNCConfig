#!/usr/bin/python

import sys
import serial
import time
import hal

POLL_TIME = 1.0         # Poll every second
MSG_LEN   = 3           # all messages have 3 byte body.
STX       = 0xAA
MSG_QUERY = 1
MSG_SET   = 2

if len(sys.argv) != 3:
    print "usage: heater.py [name] [device_path]"
    sys.exit()

component_name = sys.argv[1]
port = sys.argv[2]

print "heater: Starting Heater port=", port, " name=", component_name

# open the serial port to the platform
ser = serial.Serial()
ser.port = port
ser.baudrate = 19200
ser.timeout = 0
ser.xonxoff = False
print "heater: Opening port"
ser.open()
if not ser.isOpen():
   print "heater: Failed to open serial port"
   sys.exit()

# create hal pins
c = hal.component(component_name)
c.newpin("run",      hal.HAL_BIT,   hal.HAL_IN)
c.newpin("running",  hal.HAL_BIT,   hal.HAL_OUT)
c.newpin("ready",    hal.HAL_BIT,   hal.HAL_OUT)
c.newpin("set-temp", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("temp",     hal.HAL_FLOAT, hal.HAL_OUT)
c.newpin("actual-set-temp", hal.HAL_FLOAT, hal.HAL_OUT)

# last values of the input or input/output pins
last_run = 0
last_set_temp = 0
last_poll_time = 0

WAIT_FOR_STX=1
WAIT_FOR_MSG=2
WAIT_FOR_CHKSUM=3
state = WAIT_FOR_STX
byte_count = 0
chksum = 0
msg_body = [0,0,0]

def crc_ibutton_update( crc, data ):
    crc = crc ^ data

    for i in range(8):
        if (crc & 0x01) != 0:
            crc = (crc >> 1) ^ 0x8C
        else:
            crc = crc >> 1
    return crc


def AddChecksum( data ):
    chksum = 0
    for i in range(1,4):
        chksum = crc_ibutton_update( chksum, data[i])
    data[4] =  chksum % 256

def SendChange():
    run = int(c["run"])
    set_temp = int(c["set-temp"])
    data =  bytearray([STX, MSG_SET, set_temp % 256, run % 256, 0])
    AddChecksum( data )
    ser.write(''.join(chr(b) for b in data))

def SendQuery():
    data =  bytearray([STX, MSG_QUERY, 0, 0, 0])
    AddChecksum( data )
    ser.write(''.join(chr(b) for b in data))

def ProcessSerialPort():
    global byte_count, chksum, msg_body, state, c, last_set_temp, last_run
    while ser.inWaiting() > 0:
        b = ord(ser.read(1))

        if state == WAIT_FOR_STX:
            if b == STX:
                byte_count = 0
                chksum = 0
                state = WAIT_FOR_MSG

        elif state == WAIT_FOR_MSG:
            chksum = crc_ibutton_update( chksum, b )
            msg_body[byte_count] = b
            byte_count = byte_count + 1
            if byte_count == MSG_LEN:
                state = WAIT_FOR_CHKSUM

        elif state == WAIT_FOR_CHKSUM:
            if b == chksum:
                c["temp"] = msg_body[1]
                if msg_body[2] & 2 == 0:
                    c["running"] = 0
                else:
                    c["running"] = 1
                c["ready"] = msg_body[2] & 1
                last_set_temp = msg_body[0]
                c["actual-set-temp"] = last_set_temp
                last_run = c["running"]
            else:
                print "Checksum failed.  Got", b, "expected",  chksum
            state = WAIT_FOR_STX



# main loop
print "heater: Ready"
c.ready()
try:
    while 1:
        time.sleep(0.1)
        
        ProcessSerialPort()

        # Update input pins
        if c["run"] != last_run or \
           c["set-temp"] != last_set_temp:
            SendChange()

        now = time.time()
        if now - last_poll_time >= POLL_TIME:
            last_poll_time = now
            SendQuery()


except KeyboardInterrupt:
    pass
finally:
    pass

c.exit()
print "heater: Exiting"
