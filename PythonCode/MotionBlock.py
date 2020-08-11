MotionCount = 0
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
MotionStart(${モーションを再生する})
#動作完了まで待つ
while(MotionCount != -1):
  wait_ms(1)
