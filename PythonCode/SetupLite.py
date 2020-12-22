from i2c_bus import get as i2c_bus_get, M_BUS as i2c_bus_M_BUS
from math import floor as math_floor
from machine import Pin as machine_Pin
from neopixel import NeoPixel as neopixel_NeoPixel
from time import ticks_ms as time_ticks_ms
Library_ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
Library_ServoBeforeValue = [0] * 8
Library_i2c = i2c_bus_get(i2c_bus_M_BUS)
Library_np = neopixel_NeoPixel(machine_Pin(26), 2)
Library_ServoCurrentValue = [0] * 8
Library_CurrentLEDValue = [(0, 0, 0), (0, 0, 0)]
Library_ServoErrorFlag = False
for i in range(8):
    Library_ServoCurrentValue[i] = Library_ServoDefaultValue[i]
def Library_write8(addr, value):
    global Library_ServoErrorFlag
    try:
        cmd = bytearray(2)
        cmd[0] = addr
        cmd[1] = value
        Library_i2c.writeto(0x6A, cmd)
    except:
        Library_ServoErrorFlag = True
def Library_read8(ReadByteFrom, length):
    global Library_ServoErrorFlag
    try:
        _data = bytearray(2)
        _data[0] = ReadByteFrom >> 8
        _data[1] = ReadByteFrom & 0xFF
        Library_i2c.writeto(0x56, _data)
        return Library_i2c.readfrom(0x56, length)
    except:
        Library_ServoErrorFlag = True
def Library_servoWrite(num, degrees):
    value = math_floor(degrees * 100 * 226 / 10000) + 0x66
    Library_write8(0x08 + num * 4, value)
    if (value > 255):
        Library_write8(0x08 + num * 4 + 1, 0x01)
    else:
        Library_write8(0x08 + num * 4 + 1, 0x00)
def Library_setAngle(angle, Library_time):
    global Library_ServoCurrentValue
    step = [0] * 8
    Library_time /= 25
    for i in range(8):
        target = Library_ServoDefaultValue[i] - angle[i]
        if(target != Library_ServoCurrentValue[i]):
            step[i] = (target - Library_ServoCurrentValue[i]) / Library_time
    for n in range(Library_time):
        BeforeTime = time_ticks_ms()
        for m in range(8):
            Library_ServoCurrentValue[m] += step[m]
            Library_servoWrite(m, Library_ServoCurrentValue[m] / 10)
        while(time_ticks_ms() - BeforeTime < 25):
            wait_ms(1)
def Library_SetLED(mode, R, G, B):
    global Library_CurrentLEDValue
    if mode == 1:
        Library_CurrentLEDValue[0] = list(map(int, [G, R, B]))
    elif mode == 2:
        Library_CurrentLEDValue[1] = list(map(int, [G, R, B]))
    else:
        Library_CurrentLEDValue[0] = list(map(int, [G, R, B]))
        Library_CurrentLEDValue[1] = list(map(int, [G, R, B]))
    Library_np[0] = Library_CurrentLEDValue[0]
    Library_np[1] = Library_CurrentLEDValue[1]
    Library_np.write()
def Library_SetServo(ServoAngleArray, Time):
    Library_setAngle(ServoAngleArray, Time)
    Library_PlayFlag = False
def Library_ServoSetUp():
    global Library_ServoErrorFlag, Library_ServoCurrentValue
    try:
        for i in range(8):
            Library_ServoCurrentValue[i] = Library_ServoDefaultValue[i]
        Library_ServoErrorFlag = False
        Library_write8(0xFE, 0x85)
        Library_write8(0xFA, 0x00)
        Library_write8(0xFB, 0x00)
        Library_write8(0xFC, 0x66)
        Library_write8(0xFD, 0x00)
        Library_write8(0x00, 0x01)
        Library_setAngle([0] * 8, 100)
        Library_SetLED(0, 0, 50, 0)
        Library_ServoErrorFlag = False
    except:
        Library_ServoErrorFlag = True
Library_ServoSetUp()
