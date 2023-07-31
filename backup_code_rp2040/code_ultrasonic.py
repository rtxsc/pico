import time
import board
import adafruit_hcsr04
import simpleio

sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.GP26, echo_pin=board.GP27)
PIEZO_PIN = board.GP22
print("Hello")
simpleio.tone(PIEZO_PIN, 800, duration=0.1)
while True:
    d = sonar.distance
    try:
        print(d)
        if(d < 10):
            simpleio.tone(PIEZO_PIN, 800, duration=0.1)
        
    except RuntimeError:
        print("Retrying!")
    time.sleep(0.1)