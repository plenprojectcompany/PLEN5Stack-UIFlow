Library_i2c = Library_i2c(scl=Pin(22), sda=Pin(21), freq=400000)
Library_np = neopixel.NeoPixel(machine.Pin(26), 2)
try:
  Library_MotionSpeed
except NameError:
  Library_MotionSpeed = 100
Library_MotionStart(${モーションを再生する},Library_MotionSpeed)
