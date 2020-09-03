i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
np = neopixel.NeoPixel(machine.Pin(26), 2)
try:
  MotionSpeed
except NameError:
  MotionSpeed = 100
MotionStart(${モーションを再生する},MotionSpeed)
