from machine import Pin
from time import sleep
import utime

red = Pin(19, Pin.OUT)
grn = Pin(20, Pin.OUT)
blu = Pin(21, Pin.OUT)
led = Pin(25, Pin.OUT)

red.off()
grn.off()
blu.off()
epoch = 1671790536
while True:
    epoch = epoch + 1
    print("Toggle at " + str(utime.gmtime(epoch)))
    led.toggle()
    red.off()
    blu.toggle()
    sleep(0.5)
    led.toggle()
    blu.off()
    red.toggle()
    sleep(0.5)