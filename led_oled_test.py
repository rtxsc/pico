from machine import Pin, I2C
from utime import sleep_ms

from oled import Write, GFX, SSD1306_I2C

i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
# i2c=I2C(0,sda=Pin(16), scl=Pin(17), freq=400000)
# i2c=I2C(0,sda=Pin(20), scl=Pin(21), freq=400000)


missing_oled = False

i2c_str = "No i2c"

led = Pin(25, Pin.OUT)


def init_oled():
    oled.fill(0)
    oled.text('i2c'+i2c_str[4:5], 0, 0, 1)
    oled.text('('+i2c_str[4:5]+')', 0, 8, 1)
    oled.text(i2c_str[20:34], 0, 16, 1)
    oled.text('MicroPython', 40, 0, 1)
    oled.text('Flight Mode', 40, 8, 1)
    oled.text('NEO-M8N GPS', 40, 24, 1)
    oled.text('23 JUN 2023', 40, 36, 1)
    for i in range(0,128,5):
        oled.text(">", i, 50)
        oled.show()
        sleep_ms(10)
    oled.fill(0)

def scan_i2c():
    global devices, device, i2c_str, missing_oled
    try:
        i2c_str = str(i2c)

        # Print out any addresses found
        print(i2c)
        devices = i2c.scan()

        if len(devices) == 0:
            print("No i2c device !")
        else:
            print('i2c devices found:',len(devices))

        for device in devices:
            print("Decimal address: ",device," | Hex address: ",hex(device))
        
        if len(devices) != 0:
            if(hex(device) == hex(0x3c)):
                print("[OK] SSD1306 Found!")
        else:
            missing_oled = True
            print("[WARNING] SSD1306 Not Found!")
                          
    except OSError:
        print("OSError: [Errno 5] EIO - inside scan_i2c function")


try:
    scan_i2c()
    if not missing_oled:
        print("Init OLED")
        oled = SSD1306_I2C(128, 64, i2c)
        init_oled()
        print("Init OLED completed!")
        
except OSError:
    print("OSError: [Errno 5] EIO")
    if len(devices) != 0:
        if(hex(device) == hex(0x3c)):
            print("SSD1306 found at {} but need to unplug USB to hard-reset i2c bus".format(hex(device)))
    else:
        print("Proceed with main ignoring missing i2c devices")
    
while True:
    led.toggle()
    sleep_ms(100)