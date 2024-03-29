# Raspberry Pi Pico 
# Uploaded with Visual Studio Code via Pico-W-Go 23 Dec 2022 Friday
# Speed Gauge Addition 3 Feb 2023 Friday
# 19:54:00
# edited for Airplane Speed Testing 27 Feb 2023
# added machine.reset() at Exception 8 Mar 2023
# backup 23 June 2023 Friday 19:14
# edited 6 Oct to simplify display (minimalist)
# cool looking speed gauge using vline function

from machine import Pin, UART, I2C, SPI, WDT
# from ssd1306 import SSD1306_I2C # deleted 27 Feb 2023
from oled import Write, GFX, SSD1306_I2C
from oled.fonts import ubuntu_mono_15, ubuntu_mono_20
import tm1637
import utime, time
import math
import max7219
from hcsr04 import HCSR04
import _thread


FAULTY_FLASH_MEM = True # True on Neo-M8N | Maybe False on V.KEL and Neo-M6N
PERFORM_DEBUG = False

default_baud = 9600 # default baudrate by ublox
GPS_TX = 8 # added 28 June 2023 at TBS
GPS_RX = 9 # added 28 June 2023 at TBS
# PLEASE NOTE THAT THE VARIABLE baud ONLY USED HERE
gpsModule = UART(1, baudrate=default_baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn
print(gpsModule)

##########################################################################
import rp2, array

tm1637_connected = False
max7219_connected = True
hcsr04_connected = False
lidar_connected = False

NUM_LEDS = 12
PIN_NUM = 6
brightness = 0.2

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
 
 
# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))
 
# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)
 
# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    time.sleep_ms(10)
 
def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]
 
def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)
 
def color_chase(color, wait):
    for i in range(NUM_LEDS):
        pixels_set(i, color)
        time.sleep(wait)
        pixels_show()
    time.sleep(0.2)
 
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)
 
 
def rainbow_cycle(wait):
    for j in range(64):
        for i in range(NUM_LEDS):
            rc_index = (i * 64 // NUM_LEDS) + j
            pixels_set(i, wheel(rc_index & 64))
        pixels_show()
        time.sleep(wait)
 
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (RED, GREEN, BLUE)

for color in COLORS:       
    pixels_fill(color)
    pixels_show()
    time.sleep(0.2)
 
# print("chases")
# for color in COLORS:       
#     color_chase(color, 0.01)
##########################################################################

"""
SPI0
2 SCK - CLK on Matrix
3 TX - DIN on Matrix
5 CSn - CS on Matrix # initially 9 change to 5

GPS - UART1
gpsModule = UART(1, baudrate=baud, tx=Pin(8), rx=Pin(9))
gpsModule = UART(1, baudrate=baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn


"""

if max7219_connected:
    spi0 = SPI(0,sck=Pin(2),mosi=Pin(3)) # SCK = CLK || TX = DIN(mosi) || cs = CSn 
    cs = Pin(5, Pin.OUT) # initially 9 change to 5

    spi1 = SPI(1,sck=Pin(10),mosi=Pin(11)) # SCK = CLK || TX = DIN(mosi) || cs = CSn 
    cs2 = Pin(13, Pin.OUT)

    velo_disp 	= max7219.Matrix8x8(spi1, cs2, 4)
    prox_disp 	= max7219.Matrix8x8(spi0, cs, 4)
    velo_disp.brightness(15)
    prox_disp.brightness(15)
    velo_disp.fill(0)
    prox_disp.fill(0)
    velo_disp.show()
    prox_disp.show()

if hcsr04_connected:
    sensor = HCSR04(trigger_pin=26, echo_pin=27, echo_timeout_us=1000000)
    
if lidar_connected:
    lidar = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))    #Define receiving interface of Lidar 
    print(lidar)
    utime.sleep_ms(100)

if tm1637_connected:
    tm = tm1637.TM1637(clk=Pin(15), dio=Pin(14))
    # all LEDS on "88:88"
    tm.write([127, 255, 127, 127])
    time.sleep(0.5)

    # all LEDS off
    tm.write([0, 0, 0, 0])
    time.sleep(0.5)


def animate_text_4ch_red(s):
    velo_disp.fill(0)
    for i in range(len(s)):
        velo_disp.text(s[i],i*8,0,1)
        velo_disp.show()
        time.sleep(0.05)
        
def animate_text_4ch_green(s):
    prox_disp.fill(0)
    for i in range(len(s)):
        prox_disp.text(s[i],i*8,1,1)
        prox_disp.show()
        time.sleep(0.05)  

MAX_CHAR_DISPLAYABLE  = 21
none_found = False
nmea_count = 0
scroll_delay = 90
lidar_timeout = 0
total = 0
average = 0.0
index = 0
list = []
read_max = 5
avg_dist = 0
stop_time = 0
car_stopping = False
speed_timeout = 0
missing_oled = False
dist = 0 # global value for LIDAR
minute = 0
sec = 0
detected = False # LiDAR animation 31 Oct
gpsTime_nocolon = "(--)" # added 20 Feb 2023
prox_cleared = False

for i in range(read_max):
    list.append(0)

red = Pin(19, Pin.OUT)
grn = Pin(20, Pin.OUT)
blu = Pin(21, Pin.OUT)


max_hit = False
pos = 0
max_y = 8 # for vline parameter 

speed_32 = 0
prev_speed = 0
speed_increase = False

def map_val(x, in_min, in_max, out_min, out_max):
  return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def speed_gauge(speed,delay):
    global max_hit, pos, speed_32, speed_increase, prev_speed, max_y

    if prev_speed < speed:
        speed_increase = True
#         prox_disp.text('.',speed_32,0,True) # increase from left | True = display pattern with LED=1
        prox_disp.vline(speed_32,int(-1/4*speed_32+8),max_y,1)
    elif prev_speed > speed:
        speed_increase = False
#         prox_disp.text('.',speed_32,0,False)# decrease from right | False = display pattern with LED=0
        prox_disp.vline(speed_32,int(-1/4*speed_32+8),max_y,0)
    else:
        speed_increase = "Constant"
        
#     speed_32 = map_val(speed,0,100,-3,28) # map from 0kmh-100kmh to -3 to 28 column on matrix
    speed_32 = map_val(speed,0,100,0,32) # mapping for triangle gauge

    prev_speed = speed 
    prox_disp.show()

    utime.sleep_ms(delay)

def scroll_dot(delay):
    global max_hit, pos
    if not max_hit:
        pos = pos+1
    else:
        pos = pos-1
    prox_disp.text('|',pos,0,1)
    prox_disp.show()
    prox_disp.fill(0)
    if pos >= 28:
        max_hit = True
    if pos <= -3:
        max_hit = False
    utime.sleep_ms(delay)

def scroll_gauge(delay):
    global max_hit, pos, max_y
    if not max_hit:
        pos = pos+1
        prox_disp.vline(pos,int(-1/4*pos+8),max_y,1) # pos,y,max_y,enable
    else:
        pos = pos-1
        prox_disp.vline(pos,int(-1/4*pos+8),max_y,0) # pos,y,max_y,enable

#     prox_disp.text('|',pos,0,1)
    """
    for y = 8 , no line
    for y = 0 , full line
    when i = 0, y = 8
    when i = 32, y = 0
    """
#     for i in range(0,32):
#         prox_disp.vline(i,int(-1/4*i+8),max_y,1) # pos,y,max_y,enable
#     prox_disp.fill_rect(20,1,4,5,1) # pos,offset,xl,yl,offset
    prox_disp.show()
#     prox_disp.fill(0)
    if pos >= 32:
        max_hit = True
    if pos <= 0:
        max_hit = False
    utime.sleep_ms(delay)
    
def scroll_text_shift_half(sl,sr,delay):
    sr = sr + "                " # add empty spaces before and after str
    sl = sl + "                "
    array_sr = []
    array_sl = []
    prox_disp.fill(1)
    prox_disp.show()
    for i in range((len(sr)+len(sl))/2):
        array_sr.append(sr[i])
        array_sl.append(sl[i])
        for j in range((len(array_sl)+len(array_sr))/2):
            posRS = 14+j*7 # pos = 24+j*8
            posLS = 2+j*8 # pos = 24+j*8
            prox_disp.text(array_sr[j],posRS+i*1,1,1) 	#             prox_disp.text(array[j],pos-i*8,1,1)
            prox_disp.text(array_sl[j],posLS-i*1,1,1) 	#             prox_disp.text(array[j],pos-i*8,1,1)
            prox_disp.show()
        prox_disp.fill(0)        
        utime.sleep_ms(delay)
    array_sr.clear()
    array_sl.clear()
    
def disp_stop_elapse(m,s):
    velo_disp.fill(0)
    if(s < 10):
        velo_disp.text(str(m),0,0,1)
        velo_disp.text('m',8,0,1)
        velo_disp.text(str(s),24,0,1)
    else:
        velo_disp.text(str(m),0,0,1)
        velo_disp.text('m',8,0,1)
        velo_disp.text(str(s),16,0,1)
#     if(s < 10):
#         velo_disp.text('T+',0,0,1)
#         velo_disp.text(str(s),24,0,1)
#     else:
#         velo_disp.text('T+',0,0,1)
#         velo_disp.text(str(s),16,0,1)
    velo_disp.show()
    
def disp_distance_dot4d(d):
    prox_disp.fill(0)
    d_float = float(d)/100
    prox_disp.text(str(d_float)[0:3],0,0,1)
    prox_disp.text('m',24,0,1)
    prox_disp.show()

def static_text_prox_top(s):
    velo_disp.fill(0)
    velo_disp.text(s,0,0,1)
    velo_disp.show()
    
def static_text_prox_bottom(s):
    prox_disp.fill(0)
    prox_disp.text(s,0,0,1)
    prox_disp.show()  

def disp_speed_dot4d(speed_kmh):
    velo_disp.fill(0)
    if(speed_kmh < 10):
        velo_disp.text(' ',0,0,1)
        velo_disp.text(str(speed_kmh),24,0,1)
    elif(speed_kmh >= 10 and speed_kmh < 100):
        velo_disp.text(' ',0,0,1)
        velo_disp.text(str(speed_kmh),16,0,1)
    else:
        velo_disp.text(' ',0,0,1)
        velo_disp.text(str(speed_kmh),8,0,1)
    velo_disp.show()  

def disp_retry_dot4d(n):
    velo_disp.fill(0)
    if(n < 10):
        velo_disp.text('R',0,0,1)
        velo_disp.text(str(n),24,0,1)
    elif(n >= 10 and n < 100):
        velo_disp.text('R',0,0,1)
        velo_disp.text(str(n),16,0,1)
    else:
        velo_disp.text('R',0,0,1)
        velo_disp.text(str(n),8,0,1)
    velo_disp.show()

    
def scroll_text_bounce(s,delay):
    s = "    " + s + "    " # add empty spaces before and after str
    array = []
    prox_disp.fill(0)
    for i in range(len(s)):
        array.append(s[i])
        for j in range(len(array)):
            pos = 24+j*8
            prox_disp.text(array[j],pos-i*8,1,1)
            prox_disp.show()
        prox_disp.fill(0)        
        utime.sleep_ms(delay)  

    for i in range(len(s)):  
        for j in range(len(array)):
            pos = 8+j*8-(len(s)*8)
            prox_disp.text(array[j],pos+i*8,1,1)
            prox_disp.show()
        prox_disp.fill(0)        
        utime.sleep_ms(delay)
        
def scroll_one_way_bottom(s,delay):
    s = s + "    " # add empty spaces before and after str
    array = []
    prox_disp.fill(0)
    for i in range(len(s)):
        array.append(s[i])
        for j in range(len(array)):
            pos = 24+j*8
            prox_disp.text(array[j],pos-i*8,1,1)
            prox_disp.show()
        utime.sleep_ms(delay)
        prox_disp.fill(0)        
    array.clear()
    
def scroll_one_way_top(s,delay):
    s = s + "    " # add empty spaces before and after str
    array = []
    velo_disp.fill(0)
    for i in range(len(s)):
        array.append(s[i])
        for j in range(len(array)):
            pos = 24+j*8
            velo_disp.text(array[j],pos-i*8,1,1)
            velo_disp.show()
        utime.sleep_ms(delay)
        velo_disp.fill(0)        
    array.clear()
    
def blu_on():
    red.value(0)
    grn.value(0)
    blu.value(1)

def grn_on():
    red.value(0)
    grn.value(1)
    blu.value(0)

def red_on():
    red.value(1)
    grn.value(0)
    blu.value(0)
    
def rgb_off():
    red.value(0)
    grn.value(0)
    blu.value(0)
    
def play_rgb():
    red.value(1)
    time.sleep(0.1)
    red.value(0)
    time.sleep(0.1)

    grn.value(1)
    time.sleep(0.1)
    grn.value(0)
    time.sleep(0.1)

    blu.value(1)
    time.sleep(0.1)
    blu.value(0)
    time.sleep(0.1)

play_rgb()

osd_delay 	= 10
buff 		= bytearray(255)
TIMEOUT_SEC = 2
TIMEOUT 	= False
FIX_STATUS 	= False

latitude 	= "-1"
longitude 	= "-1"
satellites 	= "-1"
altitude_m  = "-1"
altitude_ft = "-1"
GPStime 	= "-1"
speed_gpvtg = "-1"
speed_7seg 	= 0
speed_kmh 	= 0
speed_knot	= 0
retry 		= 0
valueError  = 0

try:
    i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
    oled = SSD1306_I2C(128, 64, i2c)
    write15 = Write(oled, ubuntu_mono_15)
    write20 = Write(oled, ubuntu_mono_20)
except OSError:
    if max7219_connected:
        animate_text_4ch_red('i2c')
        animate_text_4ch_green('err')
    missing_oled = True
    

def init_oled():
    oled.fill(0)
#     oled.fill_rect(0, 0, 32, 32, 1)
#     oled.fill_rect(2, 2, 28, 28, 0)
#     oled.vline(9, 8, 22, 1)
#     oled.vline(16, 2, 22, 1)
#     oled.vline(23, 8, 22, 1)
#     oled.fill_rect(26, 24, 2, 4, 1)
    oled.text('MicroPython', 40, 0, 1)
    oled.text('Drive Mode!', 40, 8, 1)
    oled.text('NEO-M8N GPS', 40, 24, 1)
    oled.text('23 JUN 2023', 40, 36, 1)
    for i in range(0,128,5):
        oled.text(":", i, 50)
        oled.show()
        utime.sleep_ms(10)
    oled.fill(0)


def convertToDegree(RawDegrees):
    global valueError
    try:
        RawAsFloat = float(RawDegrees)
        firstdigits = int(RawAsFloat/100) 
        nexttwodigits = RawAsFloat - float(firstdigits*100) 
        
        Converted = float(firstdigits + nexttwodigits/60.0)
        Converted = '{0:.6f}'.format(Converted) 
        return str(Converted)
    except Exception as e:
        valueError += 1
        print("Exception in convertToDegree:" + str(e))
        oled.fill(0)
        oled.text("e: "+str(e), 0, 0)
        oled.text("ValueErr: "+str(valueError), 0, 10)
        oled.show()
        return "invalid"


def get_distance():
    global total, average, index, list, read_max
    distance = sensor.distance_cm()
    distance = int(distance)
    
    list.pop(0)
    list.append(distance)
    total = sum(list)
    index += 1
    
    if(index >= read_max):
        index = 0
    average = total / read_max
    return average

def async_getgps(gpsModule):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, GPStime, speed_knot, altitude_m, altitude_ft
    global retry, speed_kmh, speed_7seg, speed_gpvtg, valueError, none_found, nmea_count
    global stop_time, car_stopping, minute, sec # added 14 Oct MKE2 & 28 Oct (minute)
    global gpsTime_nocolon, prox_cleared # added 20 Feb 2023
    

    timeout = time.time() + TIMEOUT_SEC
    if(new_baud == 9600):
        NAV_FREQ_HZ = 1 # for baud 9600
    else:
        NAV_FREQ_HZ = 10 # for baud 115200
    UPDATE_RATE_MS = 1000/(NAV_FREQ_HZ*100) # NAV_FREQ_HZ*50 
    while True:
        buff = str(gpsModule.readline())
        parts = buff.split(',')
#         if(parts[0] == "b'$GPGGA" or parts[0] == "b'$GNGGA"): # commented 1 March 2023
        if(parts[0] == "b'$GPGGA" or parts[0] == "b'$GNGGA"):
            nmea_count = nmea_count + 1 # repositioned here 1 March 2023
            if(parts[1] and len(parts[1])==9):
                if "$GNRMC" in parts[1] or "$GPRMC" in parts[1]:
                    pass
                else:
                    hour = int(parts[1][0:2])
                    hour += 8
                    if hour >= 24:
                        hour = hour - 24
                        GPStime = '0'+str(hour) + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                        gpsTime_nocolon = '0'+str(hour) + parts[1][2:4]
                    else:
                        GPStime = str(hour) + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                        gpsTime_nocolon = str(hour) + parts[1][2:4]
                    
                    
        if((parts[0] == "b'$GPVTG" and len(parts) == 10) or (parts[0] == "b'$GNVTG" and len(parts) == 10)):
            if(parts[5] and parts[7]):
                speed_knot = parts[5]
                speed_gpvtg = parts[7]
                try:
                    speed_kmh = float(speed_gpvtg)
                    speed_7seg = float(parts[7])
                    if not max7219_connected: # edited 6 oct
                        speed_gauge(int(speed_kmh),1)
                except ValueError:
                    speed_7seg = -1
                    speed_kmh = -1
                if(int(speed_7seg) == 0):
                    if max7219_connected:
                        if(time.time() % 2 == 0):
                            static_text_prox_bottom("----")
#                             static_text_prox_bottom(gpsTime_nocolon)
                        else:
                            static_text_prox_bottom("    ")
                        
                    if not car_stopping:
                        stop_time = utime.time()
                        car_stopping = True
                        prox_cleared = False
                    elapse  = utime.time() - stop_time
                    elapse = elapse % (24 * 3600)
                    hour = elapse // 3600
                    sec = elapse % 3600
                    minute = sec // 60
                    sec %= 60
                    
                    if max7219_connected:
                        if elapse <= 1:
#                             animate_text_4ch_red('STOP')
                            scroll_text_shift_half('<<','>>',10)
                        else:
                            pass
#                             disp_stop_elapse(int(minute),int(sec))
#                             animate_text_4ch_red('STOP')


#                         if(elapse % 2 == 0):
#                             static_text_prox_top('   ')
#                         else:
#                             static_text_prox_top('STOP')
                
#                     if(elapse >=15 and elapse % 15 == 0):
#                         scroll_one_way_top('SatNum: '+satellites,100)   
#                     if(elapse >=30 and elapse % 30 == 0):
#                         scroll_one_way_top('GPS Time: '+GPStime,100)                        
                else:
                    car_stopping = False
                    if not prox_cleared:
                        if max7219_connected:
                            prox_disp.fill(0)
                            prox_disp.show()
                        prox_cleared = True
                    if max7219_connected:
                        disp_speed_dot4d(int(speed_7seg))
                break
     


        if ((parts[0] == "b'$GPGGA" and len(parts) == 15) or (parts[0] == "b'$GNGGA" and len(parts) == 15)):
#             print(buff + "\t" + str(speed_kmh) + " km/h")
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                if "$GNRMC" in parts[2] or "$GPRMC" in parts[2] or "$GNRMC" in parts[4] or "$GPRMC" in parts[4]:
                    pass
                else:
                    blu_on()
                    latitude = convertToDegree(parts[2])
                    if (parts[3] == 'S'):
                        latitude = -latitude
                    longitude = convertToDegree(parts[4])
                    if (parts[5] == 'W'):
                        longitude = -longitude
                    satellites = parts[7]
                    try:
                        altitude_m = int(float(parts[9]))
                        altitude_ft = int(altitude_m * 3.28084)
                    except:
                        print("Unable to parse parts[9] for the altitude")
                        pass
                
                try:
                    hour = int(parts[1][0:2])
                    hour += 8
                    if hour >= 24:
                        hour = hour - 24
                        GPStime = '0'+str(hour) + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                    else:
                        GPStime = str(hour) + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                except:
                    pass
                FIX_STATUS = True # FIX_STATUS determined by parts[6] = Position Fix Indicator
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        utime.sleep_ms(int(UPDATE_RATE_MS)) # last line of while True loop
        
    display_mode = 1

    if(FIX_STATUS == True):
        rgb_off()
        if not missing_oled:
            oled.fill(0)
            if display_mode == 0:
                if(time.time() % 2 == 0):
                    oled.text("Lat: "+str(latitude), 0, 0) # TypeError: can't convert 'NoneType' object to str implicitly = Quick fix explicit conversion to str()
                    oled.text("Lng: "+str(longitude), 0, 8) # TypeError: can't convert 'NoneType' object to str implicitly = Quick fix explicit conversion to str()
                else:
                    oled.text("Alt: "+str(altitude_m)+" m", 0, 0)
                    oled.text("Alt: "+str(altitude_ft)+" ft", 0, 8)
            else:
                oled.text(str(latitude[0:6])+" "+str(longitude[0:9]), 0, 0)
#                 speed_kmh = 840.50
#                 altitude_m = 9144
#                 altitude_ft = 30000
                oled.text(str(altitude_m)+"m / "+str(altitude_ft)+"ft", 0, 8)
            oled.text("Sat: "+satellites+ "| V:"+ speed_knot, 0, 20)
            oled.text("GMT: "+GPStime, 0, 30)
            write20.text("VK: "+str(int(speed_kmh)) + " km/h", 0, 40)
            oled.show()
     
        FIX_STATUS = False
        none_found = False

    if(TIMEOUT == True): # timeout reached due to no fix
        red_on()
        pixels_fill(RED)
        if not missing_oled:      
            oled.fill(0)
            oled.text("No GPS found", 0, 0)
            oled.text("Time:"+ GPStime, 0, 9)
            oled.text("ValueErr:"+str(valueError), 0, 20)
            write20.text("No Fix:" + str(retry), 0, 30)
            oled.text("NMEA:" + str(nmea_count/60), 0, 50)
            oled.show()
        
        if max7219_connected:
            scroll_one_way_top("Searching: "+str(retry),100)
            if(time.time() % 2 == 0):
                static_text_prox_bottom(gpsTime_nocolon)
            else:
                static_text_prox_bottom("(00)")
            
        retry += 1
        if(retry >= 10):
            if not missing_oled:      
                oled.fill(0)
                oled.text("GPS Failed", 0, 0)
                oled.text("Reboot", 0, 10)
                oled.show()
                utime.sleep_ms(1000)
            if max7219_connected:
                scroll_one_way_top("Reboot ",100)
                scroll_one_way_top("////",100)
            machine.reset() # added logic 20 Feb 2023
        
   
        TIMEOUT = False

def set_update_1hz():
#     print("set_update_1hz...")
    info_packet = "B5 62 06 08 06 00 E8 03 01 00 01 00 01 39"
    ubx_cfg_rate = "B5 62 06 08 00 00 0E 30"
    info_packet = info_packet + " " + ubx_cfg_rate
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 1 Hz config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Change update rate:", 0, 0)
        write15.text("1 kHz", 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)

def set_update_5hz():
#     print("set_update_5hz...")
    info_packet = "B5 62 06 08 06 00 C8 00 01 00 01 00 DE 6A"
    ubx_cfg_rate = "B5 62 06 08 00 00 0E 30"
    info_packet = info_packet + " " + ubx_cfg_rate
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 5 Hz config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Change update rate:", 0, 0)
        write15.text("5 kHz", 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)

def set_update_10hz():
#     print("set_update_10hz...")
    info_packet = "B5 62 06 08 06 00 64 00 01 00 01 00 7A 12"
    ubx_cfg_rate = "B5 62 06 08 00 00 0E 30"
    info_packet = info_packet + " " + ubx_cfg_rate
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 10 Hz config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Change update rate:", 0, 0)
        write15.text("10 kHz", 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)

def change_baud_921600(prev_baud):
    global gpsModule, new_baud, GPS_RX, GPS_TX
    new_baud=921600
    if prev_baud != new_baud and not missing_oled:
        oled.fill(0)
        oled.text("baud changing", 0, 20)
        oled.show()
        utime.sleep_ms(osd_delay)
        
    if not missing_oled:
        oled.fill(0)
        oled.text("Prev baud:", 0, 0)
        write15.text(str(prev_baud), 0, 10)
        oled.text("New baud:", 0, 30)
        write15.text(str(new_baud), 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Change baud to:", 0, 0)
        write15.text(str(prev_baud) +"->"+ str(new_baud), 0, 40)
        oled.show()
    utime.sleep_ms(osd_delay)
    print("Change baud setting to 921600...")
    info_packet = "B5 62 06 00 14 00 01 00 00 00 D0 08 00 00 00 10 0E 00 07 00 03 00 00 00 00 00 1B 5A"
    ubx_cfg_prt = "B5 62 06 00 01 00 01 08 22"
    info_packet = info_packet + " " + ubx_cfg_prt
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 921600 config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Sending command", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Reinitialize UART1", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    gpsModule = UART(1, baudrate=new_baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn
    print(gpsModule)
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Saving to file", 0, 0)
        write15.text(str(new_baud)+"->file", 0, 40)
        oled.show()
    file = open("saves.txt", "w")
    print("Saving 921600 config into memory")
    file.write(str(new_baud))
    file.close()
    utime.sleep_ms(osd_delay)

def change_baud_460800(prev_baud):
    global gpsModule, new_baud, GPS_RX, GPS_TX
    new_baud=460800
    if prev_baud != new_baud and not missing_oled:
        oled.fill(0)
        oled.text("baud changing", 0, 20)
        oled.show()
        utime.sleep_ms(osd_delay)
        
    if not missing_oled:
        oled.fill(0)
        oled.text("Prev baud:", 0, 0)
        write15.text(str(prev_baud), 0, 10)
        oled.text("New baud:", 0, 30)
        write15.text(str(new_baud), 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Change baud to:", 0, 0)
        write15.text(str(prev_baud) +"->"+ str(new_baud), 0, 40)
        oled.show()
    utime.sleep_ms(osd_delay)
    print("Change baud setting to 460800...")
    info_packet = "B5 62 06 00 14 00 01 00 00 00 D0 08 00 00 00 08 07 00 07 00 03 00 00 00 00 00 0C BC"
    ubx_cfg_prt = "B5 62 06 00 01 00 01 08 22"
    info_packet = info_packet + " " + ubx_cfg_prt
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 460800 config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Sending command", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Reinitialize UART1", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    gpsModule = UART(1, baudrate=new_baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn
    print(gpsModule)
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Saving to file", 0, 0)
        write15.text(str(new_baud)+"->file", 0, 40)
        oled.show()
    file = open("saves.txt", "w")
    print("Saving 460800 config into memory")
    file.write(str(new_baud))
    file.close()
    utime.sleep_ms(osd_delay)

def change_baud_115200(prev_baud):
    global gpsModule, new_baud, GPS_RX, GPS_TX
    new_baud=115200
    if prev_baud != new_baud and not missing_oled:
        oled.fill(0)
        oled.text("baud changing", 0, 20)
        oled.show()
        utime.sleep_ms(osd_delay)
        
    if not missing_oled:
        oled.fill(0)
        oled.text("Prev baud:", 0, 0)
        write15.text(str(prev_baud), 0, 10)
        oled.text("New baud:", 0, 30)
        write15.text(str(new_baud), 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Change baud to:", 0, 0)
        write15.text(str(prev_baud) +"->"+ str(new_baud), 0, 40)
        oled.show()
    utime.sleep_ms(osd_delay)
    print("Change baud setting to 115200...")
    info_packet = "B5 62 06 00 14 00 01 00 00 00 D0 08 00 00 00 C2 01 00 07 00 03 00 00 00 00 00 C0 7E"
    ubx_cfg_prt = "B5 62 06 00 01 00 01 08 22"
    info_packet = info_packet + " " + ubx_cfg_prt
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 115200 config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Sending command", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Reinitialize UART1", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule.write(bytes(hex_lst))
    utime.sleep_ms(osd_delay)
    gpsModule = UART(1, baudrate=new_baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn
    print(gpsModule)
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Saving to file", 0, 0)
        write15.text(str(new_baud)+"->file", 0, 40)
        oled.show()
    file = open("saves.txt", "w")
    print("Saving 115200 config into memory")
    file.write(str(new_baud))
    file.close()
    utime.sleep_ms(osd_delay)

def change_baud_9600(prev_baud):
    global gpsModule, new_baud, GPS_RX, GPS_TX
    new_baud=9600
    if prev_baud != new_baud and not missing_oled:
        oled.fill(0)
        oled.text("baud changing", 0, 20)
        oled.show()
        utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Prev baud:", 0, 0)
        write15.text(str(prev_baud), 0, 10)
        oled.text("New baud:", 0, 30)
        write15.text(str(new_baud), 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)
        oled.fill(0)
        oled.text("Change baud to:", 0, 0)
        write15.text(str(prev_baud) +"->"+ str(new_baud), 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)
    print("Change baud setting to 9600...")
    info_packet = "B5 62 06 00 14 00 01 00 00 00 D0 08 00 00 80 25 00 00 07 00 03 00 00 00 00 00 A2 B5"
    ubx_cfg_prt = "B5 62 06 00 01 00 01 08 22"
    info_packet = info_packet + " " + ubx_cfg_prt
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Sending command for 9600 config")
    if not missing_oled:
        oled.fill(0)
        oled.text("Sending command", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
        gpsModule.write(bytes(hex_lst))
        utime.sleep_ms(osd_delay)
        oled.fill(0)
        oled.text("Reinitialize UART1", 0, 0)
        write15.text(str(new_baud), 0, 40)
        oled.show()
    gpsModule = UART(1, baudrate=new_baud, tx=Pin(GPS_TX), rx=Pin(GPS_RX)) # obtained pin 9 from SPI0 Csn
    print(gpsModule)
    utime.sleep_ms(osd_delay)
    if not missing_oled:
        oled.fill(0)
        oled.text("Saving to file", 0, 0)
        write15.text(str(new_baud)+"->file", 0, 40)
        oled.show()
    file = open("saves.txt", "w")
    print("Saving 9600 config into memory")
    file.write(str(new_baud))
    file.close()
    utime.sleep_ms(osd_delay)

        
def save_config():
    print("Saving config...")
    if not missing_oled:
        oled.fill(0)
        oled.text("Saving Config", 0, 0)
        oled.text("Sending Command", 0, 20)
        oled.text("Write to flash", 0, 40)

    info_packet = "B5 62 06 09 0D 00 00 00 00 00 FF FF 00 00 00 00 00 00 17 31 BF"
    info_packet = info_packet.split()
    hex_lst = []
    for i in range(len(info_packet)):
        hex_lst.append(int("0x"+info_packet[i],16))
#     print(hex_lst)
    utime.sleep_ms(osd_delay)
#     print("Writing to flash...")
    gpsModule.write(bytes(hex_lst))
    if not missing_oled:
        for i in range(0,128,5):
            oled.text("|", i, 50)
            oled.show()
            utime.sleep_ms(1)
        oled.fill(0)
        write20.text("DONE CONFIG", 0, 0)
        for i in range(0,127,4):
            oled.text("|", i, 25)
            oled.show()
            utime.sleep_ms(1)
        write20.text("BEGIN GPS", 0, 40)
        oled.show()
        utime.sleep_ms(osd_delay)

def load_baudrate():
    try:
        file = open("saves.txt")
        baud = int(file.read())
        print("loaded baudrate from memory:{}".format(baud))
        file.close()
    except OSError:
        print("new saves file created!")
        file = open("saves.txt", "w")
        baud = 9600
        file.write(str(baud))
        file.close()
    return baud


# Thread for sr04m
def async_get_distance_thread():
    global avg_dist, speed_7seg
    print("Running Proximity Thread")
    scroll_delay = 10
    while True:
#         prox_disp 	= max7219.Matrix8x8(spi0, cs, 4) # disabled 26 June 2023 after SPI0 CSn reconfig
        avg_dist = get_distance()
#         tm.number(int(avg_dist)) # give to LIDAR
        if(PERFORM_DEBUG): 
            disp_distance_dot4d(int(avg_dist))
        else:
            if(avg_dist > 500):
#                 animate_text_4ch_red('SAFE')
                scroll_one_way_bottom('SAFE',scroll_delay)
            elif(avg_dist > 450 and avg_dist < 500):
#                 animate_text_4ch_red('CARE')
                scroll_one_way_bottom('CLOSE',scroll_delay)
            else:
                disp_distance_dot4d(int(avg_dist))
        utime.sleep_ms(100)

frame_rate = 20 # default at 20Hz (best tested at 115200)

# Thread for TFmini-Plus
def getLidarData(UART0):
    global lidar_timeout, dist, detected
    bin_ascii = bytearray()
    if UART0.any() > 0:
        lidar_timeout = utime.time() + 5
        bin_ascii += UART0.read(9) # byte [0-8] = 9 bytes
        
        if PERFORM_DEBUG:
            hex_stream = hexlify(bin_ascii,' ').decode()
#             print(hex_stream[0:26]) # uncomment this to see the HEX data

        if bin_ascii[0] == 0x59 and bin_ascii[1] == 0x59 :
            distance   	= bin_ascii[2] + bin_ascii[3] * 256             #Get distance value  
            strength    = bin_ascii[4] + bin_ascii[5] * 256            	#Get Strength value  
            temperature	= (bin_ascii[6] + bin_ascii[7]* 256)/8-256
            if tm1637_connected:
                tm.number(int(strength))
            
            dist = int(distance)
            if(dist == 0 or dist >=700):
                pixels_fill(GREEN)
            elif(dist < 700 and dist > 400):
                pixels_fill(CYAN)
            else:
                pixels_fill(RED)
            pixels_show()

#             PERFORM_DEBUG = 1 # overwrite global PERFORM_DEBUG here 30 Sept 2022
            if(PERFORM_DEBUG): 
                disp_distance_dot4d(int(distance))
            else:
                if(int(distance) == 0):
                    detected = False
                    scroll_dot(0)
#                     animate_text_4ch_green('SAFE')
#                     if(utime.time() % 2 == 0):
#                         static_text_prox(' O.O')
#                     else:
#                         static_text_prox(' ^.^')
                else:
                    if not detected:
                        scroll_text_shift_half('>>','<<',50)
                        detected = True
                    disp_distance_dot4d(int(distance))
#             prox_disp = max7219.Matrix8x8(spi0, cs, 4) # to refresh SPI inside thread / disabled 26 June 2023
    if utime.time() > lidar_timeout:
        pass
#         scroll_one_way_bottom('LiDAR DISCONNECTED',scroll_delay)


def set_samp_rate(samp_rate=frame_rate):
    # change the sample rate
    global frame_rate
    print("Setting sample rate to {} Hz".format(samp_rate))
    samp_rate = int(samp_rate)
    frame_rate = samp_rate
    hex_rate = samp_rate.to_bytes(2,'big')
    print("hex_rate:{}".format(hex_rate)) # \xHH\xLL => hex_rate[0]=\xHH hex_rate[1]=\xLL 
    samp_rate_packet = [0x5a,0x06,0x03,hex_rate[1],hex_rate[0],00,00] # sample rate byte array
    for i in range(len(samp_rate_packet)):
        print(hex(samp_rate_packet[i]), end=" ")
    lidar.write(bytes(samp_rate_packet)) # send sample rate instruction
    utime.sleep(0.1) # wait for change to take effect
    save_settings()
    return

def get_version(UART0):
    # get version info | source: https://makersportal.com/blog/distance-detection-with-the-tf-luna-lidar-and-raspberry-pi
    info_packet = [0x5a,0x04,0x14,0x00]
    lidar.write(bytes(info_packet))
    start_tick = utime.time()
    print("getting lidar version")
    while (utime.time()-start_tick < 2):
        bin_ascii = bytearray()
        if UART0.any() > 0:
            bin_ascii += UART0.read(30) # known 30 bytes-length response
            if bin_ascii[0] == 0x5a:
                hex_stream = hexlify(bin_ascii,' ').decode('utf-8')
                hex_array = hex_stream.split(" ")
#                 print(hex_stream) # uncomment this to see the HEX data
#                 print("{}".format(bin_ascii.decode('utf-8')))
                version = bin_ascii[0:].decode('utf-8')
                if max7219_connected:
                    scroll_one_way_bottom(version,scroll_delay)

                lst = []
                for c in version:
                    lst.append(c)
                
                for i in range(len(hex_array)):
                    print("0x{} : ascii -> {}".format(hex_array[i],lst[i]))
                print('\nVersion -'+version+'\n')
                return
            else:
                lidar.write(bytes(info_packet))
    print("Failed to retrieve version")
    if max7219_connected:
        animate_text_4ch_green('NULL')
        prox_disp.fill(0)
                
def save_settings():
    print("\nSaving setting...")
    info_packet = [0x5a,0x04,0x11,0x6F]
    lidar.write(bytes(info_packet))
    utime.sleep_ms(100)

def lidar_thread():
    global lidar_timeout
    print("starting lidar thread")
    try:
        if max7219_connected:
            scroll_one_way_bottom('GET LiDAR',scroll_delay)
        get_version(lidar)
    except:
        # to avoid error when no TFmini-Plus connected while debugging
        pass
        
    set_samp_rate(20) # min: 1 - max: 30 
    print("\nStart measuring")
    lidar_timeout = utime.time() + 5
    while True:
        try:
            getLidarData(lidar)
        except:
            # to avoid error when no TFmini-Plus connected while debugging
            pass


# Start coroutine as a task and immediately return
def main():
#     _thread.start_new_thread(async_get_distance_thread, ())
    if not missing_oled:
        init_oled()
    if max7219_connected:
        scroll_one_way_top("||||||||||||",50)
        utime.sleep(0.5)
        animate_text_4ch_red('KUTS')
        animate_text_4ch_green('AXIA')
        prox_disp.fill(0)
    if FAULTY_FLASH_MEM:
        prev_baud = load_baudrate()
        change_baud_9600(prev_baud)
        set_update_1hz()
        prev_baud = load_baudrate()
        change_baud_115200(prev_baud) 
        prev_baud = load_baudrate()
        change_baud_460800(prev_baud)
        prev_baud = load_baudrate()
        change_baud_921600(prev_baud)
        set_update_10hz()
        save_config()
    else:
        prev_baud = load_baudrate()
        change_baud_115200(prev_baud)
        set_update_10hz()
        save_config()
    if lidar_connected:
        _thread.start_new_thread(lidar_thread, ()) # relocated here 5 Oct 2022 | Wednesday
    while 1:
        async_getgps(gpsModule)

# Start event loop and run entry point coroutine
try:
    main()
#     while 1:
#         scroll_gauge(10)
#         for i in range(0,100):
#             speed_gauge(i,10)
#         for i in range(100,0,-1):
#             speed_gauge(i,10)
except OSError:
    if max7219_connected:
        animate_text_4ch_red('WDT2')
    # discovered 14 Oct Friday after 1st Interim session CEEE111
    print("Watchdog reboot | wdt = WDT(timeout=1000)") 
    wdt = WDT(timeout=1000) # reliable restarting 
#     machine.reset() # hit or miss
    if max7219_connected:
        animate_text_4ch_green('BOOT')
    print("Restarting Pico")
    utime.sleep(0.5)


except KeyboardInterrupt:
    print("bye")
    
except Exception as e:
    # NEVER PUT WDT HERE
    # Once it is running the timeout cannot be changed and the WDT cannot be stopped either.
    # Pico will be stucked in the infinite WDT loop
    print(e)
    count = 1
    print("Captured exception: "+str(e))
    oled.fill(0)
    write20.text("EXCEPTION", 0, 0)
    msg = str(e)
    if(len(msg) > MAX_CHAR_DISPLAYABLE):
        oled.text('Exception len:'+str(len(msg)), 0, 20, True)
        for i in range(0,len(msg)):
            if(i < MAX_CHAR_DISPLAYABLE):
                oled.text(msg[0:i], 0, 30, True)
            else:
                print("extended length")
                lengthOfChar = len(msg[0:len(msg)])
                print(lengthOfChar)
                if(lengthOfChar == MAX_CHAR_DISPLAYABLE*count):
                    count += 1
                oled.text(msg[MAX_CHAR_DISPLAYABLE*count:i], 0, 40, True)
            oled.show()
        oled.show()
    else:
        oled.text('len:'+str(len(msg)), 0, 20, True)
        oled.text(msg, 0, 30, True)
        oled.show()
    machine.reset() # added 8 Mar 2023









