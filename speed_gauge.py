from machine import Pin, UART, I2C, SPI, WDT
import max7219
import utime

spi0 = SPI(0,sck=Pin(2),mosi=Pin(3)) # SCK = CLK || TX = DIN(mosi) || cs = CSn 
cs = Pin(9, Pin.OUT)

spi1 = SPI(1,sck=Pin(10),mosi=Pin(11)) # SCK = CLK || TX = DIN(mosi) || cs = CSn 
cs2 = Pin(13, Pin.OUT)

max_hit = False
posR = -5
velo_disp 	= max7219.Matrix8x8(spi1, cs2, 4)
prox_disp 	= max7219.Matrix8x8(spi0, cs, 4)
velo_disp.brightness(15)
prox_disp.brightness(15)
velo_disp.fill(0)
prox_disp.fill(0)
velo_disp.show()
prox_disp.show()

speed_32 = 0
prev_speed = 0
speed_increase = False


adc26 = machine.ADC(26)

def map_val(x, in_min, in_max, out_min, out_max):
  return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def speed_gauge(speed,delay):
    global max_hit, posR, speed_32, speed_increase, prev_speed

    if prev_speed < speed:
        speed_increase = True
        prox_disp.text('|',speed_32,0,True) # increase from left | True = display pattern with LED=1
    elif prev_speed > speed:
        speed_increase = False
        prox_disp.text('|',speed_32,0,False)# decrease from right | False = display pattern with LED=0
    else:
        speed_increase = "Constant"
        
    speed_32 = map_val(speed,0,100,-3,28)
    prev_speed = speed 
    prox_disp.show()

    utime.sleep_ms(delay)

while 1:
    pot = adc26.read_u16()
    speed = map_val(pot,200,65535,0,100)
#     print("adc:{} speed:{} gauge:{} state:{}".format(pot,speed,speed_32, speed_increase))
    speed_gauge(speed,10)
