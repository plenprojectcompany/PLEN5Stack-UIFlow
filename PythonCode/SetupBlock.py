#インポート
from machine import Pin, I2C
import re
import math
import machine, neopixel

#変数の定義
ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
MotionCache = []
CurrentLEDValue = [(0,0,0),(0,0,0)]
ServoCurrentValue = [0] * 8
ServoBeforeValue = [0] * 8
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
np = neopixel.NeoPixel(machine.Pin(26), 2)
global MotionCount
MotionCount = 0
MotionSpeed = 100

for i in range(8):
  ServoCurrentValue[i] = ServoDefaultValue[i]

#関数の定義
def write8(addr, value):
  cmd = bytearray(2)
  cmd[0] = addr
  cmd[1] = value
  i2c.writeto(0x6A, cmd)

def servoWrite(num, degrees):
  value = math.floor(degrees * 100 * 226 / 10000) + 0x66
  write8(0x08 + num * 4, value)
  if (value > 255):
    write8(0x08 + num * 4 + 1, 0x01)
  else:
    write8(0x08 + num * 4 + 1, 0x00)

def setAngle(angle,time):
  step=[0,0,0,0,0,0,0,0]
  time/=5*MotionSpeed/100
  for i in range(8):
    target = ServoDefaultValue[i] - angle[i]
    if(target != ServoCurrentValue[i]):
      step[i]=(target-ServoCurrentValue[i])/time
  for n in range(time):
    for m in range(8):
      ServoCurrentValue[m]+=step[m]
      servoWrite(m,ServoCurrentValue[m]/10)
    wait_ms(1)
  global MotionCount
  MotionCount+=1


write8(0xFE, 0x85)
write8(0xFA, 0x00)
write8(0xFB, 0x00)
write8(0xFC, 0x66)
write8(0xFD, 0x00)
write8(0x00, 0x01)
setAngle([0, 0, 0, 0, 0, 0, 0, 0], 10)

def MotionStart(MotionNumber):
    global MotionCount

    #キャッシュされているか確認
    Cache = ""
    for i in range(len(MotionCache) / 2):
      if(int(MotionCache[i * 2]) == MotionNumber):
        Cache = MotionCache[i * 2 + 1]
        break

    if(Cache == ""):
      ReadByteFrom = 50 + 860 * MotionNumber
      #モーションデータの読み取り
      _data = bytearray(2)
      _data[0] = ReadByteFrom >> 8
      _data[1] = ReadByteFrom & 0xFF
      i2c.writeto(0x56, _data)
      ReadData = i2c.readfrom(0x56, 860)
      MotionCache.append(str(MotionNumber))
      MotionCache.append(str(ReadData))
    else:
      ReadData = Cache

    #モーションデータの切り出し
    MotionDataArray = str(ReadData).split('>')
    TransitionTimeArray = []
    SearvoArray = []

    for i in MotionDataArray:
        if(re.match('^MF' + '{:02x}'.format(MotionNumber),i)):
            check1=re.match('(MF....)(....)',i)
            TransitionTimeArray.append(int(check1.group(2),16))
            for n in range(8):
                check2 = int(i[10+4*n:10+4*n+4],16)
                if check2 >= 0x7fff:
                  check2 = ~(~check2 & 0xffff)
                else:
                  check2 = check2 & 0xffff
                SearvoArray.append(check2)


    #サーボモーターを動かす
    ErrorFlag = False
    while MotionCount != len(TransitionTimeArray):
      SearvoArrayCheck = []
      for i in range(8):
        count1 = 8 * MotionCount + i
        SearvoArrayCheck.append(SearvoArray[count1])
      if(SearvoArrayCheck == ServoBeforeValue): #同じサーボ角を繰り返す場合、動作スキップする
        MotionCount+=1
      else:
        MotionCountBefore = MotionCount
        if(SearvoArrayCheck == [0,0,0,0,0,0,0,0]): #サーボを初期値に戻す場合、動作を高速化する
          setAngle(SearvoArrayCheck,10)
        else:
          setAngle(SearvoArrayCheck,TransitionTimeArray[MotionCount])
        while(MotionCount == MotionCountBefore):
          wait_ms(1)
      for i in range(8):
        ServoBeforeValue[i] = SearvoArrayCheck[i]
    MotionCount = -1
#初期化完了まで待つ
while(MotionCount != 1):
  wait_ms(1)
#セットアップ完了
