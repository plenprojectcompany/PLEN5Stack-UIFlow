MotionCount = 0
ServoAngleArray = [${Angle0}*10,${Angle1}*10,${Angle2}*-10,${Angle3}*10,${Angle4}*-10,${Angle5}*-10,${Angle6}*10,${Angle7}*-10]
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
setAngle(ServoAngleArray,${Time})
#動作完了まで待つ
while(MotionCount != 1):
    wait_ms(1)
