import i2c_bus
import math
import machine, neopixel

Library_ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
Library_CurrentLEDValue = [(0,0,0),(0,0,0)]
Library_ServoCurrentValue = [0] * 8
Library_ServoBeforeValue = [0] * 8
Library_i2c = i2c_bus.get(i2c_bus.M_BUS)
Library_np = neopixel.NeoPixel(machine.Pin(26), 2)

for i in range(8):
  Library_ServoCurrentValue[i] = Library_ServoDefaultValue[i]

def Library_write8(addr, value):
  cmd = bytearray(2)
  cmd[0] = addr
  cmd[1] = value
  Library_i2c.writeto(0x6A, cmd)

def Library_servoWrite(num, degrees):
  value = math.floor(degrees * 100 * 226 / 10000) + 0x66
  Library_write8(0x08 + num * 4, value)
  if (value > 255):
    Library_write8(0x08 + num * 4 + 1, 0x01)
  else:
    Library_write8(0x08 + num * 4 + 1, 0x00)

def Library_setAngle(angle,Library_time):
  step=[0,0,0,0,0,0,0,0]
  Library_time/=25
  for i in range(8):
    target = Library_ServoDefaultValue[i] - angle[i]
    if(target != Library_ServoCurrentValue[i]):
      step[i]=(target-Library_ServoCurrentValue[i])/Library_time
  for n in range(Library_time):
    BeforeTime=time.ticks_ms()
    for m in range(8):
      Library_ServoCurrentValue[m]+=step[m]
      Library_servoWrite(m,Library_ServoCurrentValue[m]/10)
    while(time.ticks_ms()-BeforeTime<25):
      wait_ms(1)

def Library_SetServo(ServoAngleArray,Time):
    if(Time<25):
        Time=25
    Library_setAngle(ServoAngleArray,Time)

Library_write8(0xFE, 0x85)
Library_write8(0xFA, 0x00)
Library_write8(0xFB, 0x00)
Library_write8(0xFC, 0x66)
Library_write8(0xFD, 0x00)
Library_write8(0x00, 0x01)
Library_setAngle([0, 0, 0, 0, 0, 0, 0, 0], 100)
Library_CurrentLEDValue[0] = [50, 0, 0]
Library_CurrentLEDValue[1] = [50, 0, 0]
Library_np[0] = Library_CurrentLEDValue[0]
Library_np[1] = Library_CurrentLEDValue[1]
Library_np.write()
