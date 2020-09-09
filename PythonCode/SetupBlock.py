#インポート
from machine import Pin, I2C
import re
import math
import machine, neopixel
import urequests

#変数の定義
ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
MotionNumberCache = []
TransitionTimeArrayCache = []
SearvoArrayCache = []
CurrentLEDValue = [(0,0,0),(0,0,0)]
ServoCurrentValue = [0] * 8
ServoBeforeValue = [0] * 8
i2c = I2C(scl=Pin(22), sda=Pin(21), freq=400000)
np = neopixel.NeoPixel(machine.Pin(26), 2)
MotionCount = 0

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
  time/=5
  for i in range(8):
    target = ServoDefaultValue[i] - angle[i]
    if(target != ServoCurrentValue[i]):
      step[i]=(target-ServoCurrentValue[i])/time
  for n in range(time):
    for m in range(8):
      ServoCurrentValue[m]+=step[m]
      servoWrite(m,ServoCurrentValue[m]/10)
    wait_ms(1)

def GetTime(mode):
    try:
      req = urequests.request(method='GET', url='https://ntp-a1.nict.go.jp/cgi-bin/time', headers={})
      GetData = req.text
      GetData = GetData.replace('  ', ':')
      GetData = GetData.replace(' ', ':')
      TimeList = GetData.split(':')

      if(mode == 1): #年
        return TimeList[6]
      elif(mode == 2): #月
        return TimeList[1]
      elif(mode == 3): #日
        return TimeList[2]
      elif(mode == 4): #曜日
        return TimeList[0]
      elif(mode == 5): #時
        return TimeList[3]
      elif(mode == 6): #分
        return TimeList[4]
      elif(mode == 7): #秒
        return TimeList[5]
      elif(mode == 0): #リスト
        return [TimeList[6],TimeList[1],TimeList[2],TimeList[0],TimeList[3],TimeList[4],TimeList[5]]
      else:
        return "-1"
    except:
      if(mode == 1): #年
        return "0000"
      elif(mode == 2): #月
        return "0"
      elif(mode == 3): #日
        return "0"
      elif(mode == 4): #曜日
        return "---"
      elif(mode == 5): #時
        return "00"
      elif(mode == 6): #分
        return "00"
      elif(mode == 7): #秒
        return "00"
      elif(mode == 0): #リスト
        return ["0000","0","0","---","00","00","00"]
      else:
        return "-1"

#初期化
write8(0xFE, 0x85)
write8(0xFA, 0x00)
write8(0xFB, 0x00)
write8(0xFC, 0x66)
write8(0xFD, 0x00)
write8(0x00, 0x01)
setAngle([0, 0, 0, 0, 0, 0, 0, 0], 10)
CurrentLEDValue[0] = [50, 0, 0]
CurrentLEDValue[1] = [50, 0, 0]
np[0] = CurrentLEDValue[0]
np[1] = CurrentLEDValue[1]
np.write()
MotionSpeed = 100

def MotionStart(MotionNumber,Speed):
    MotionCount = 0

    if(MotionNumber in MotionNumberCache): #キャッシュされているか確認
      CacheNumber = MotionNumberCache.index(MotionNumber)
      #キャッシュから取得する
      TransitionTimeArray = TransitionTimeArrayCache[CacheNumber]
      SearvoArray = SearvoArrayCache[CacheNumber]
    else:
      #モーションデータの読み取り
      ReadByteFrom = 50 + 860 * MotionNumber
      _data = bytearray(2)
      _data[0] = ReadByteFrom >> 8
      _data[1] = ReadByteFrom & 0xFF
      i2c.writeto(0x56, _data)
      ReadData = i2c.readfrom(0x56, 860)

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
      #読み込んだデータはキャッシュする
      MotionNumberCache.append(MotionNumber)
      TransitionTimeArrayCache.append(TransitionTimeArray)
      SearvoArrayCache.append(SearvoArray)

    #サーボモーターを動かす
    ErrorFlag = False
    while MotionCount != len(TransitionTimeArray):
      SearvoArrayCheck = []
      for i in range(8):
        count1 = 8 * MotionCount + i
        SearvoArrayCheck.append(SearvoArray[count1])
      if(ServoBeforeValue == SearvoArrayCheck): #同じサーボ角を繰り返す場合、動作スキップする
        MotionCount+=1
      else:
        MotionCountBefore = MotionCount
        setAngle(SearvoArrayCheck,TransitionTimeArray[MotionCount]/(Speed / 100))
        wait_ms(int(TransitionTimeArray[MotionCount]/(Speed / 100) / 5))
        MotionCount += 1
      for i in range(8):
        ServoBeforeValue[i] = SearvoArrayCheck[i]
    MotionCount = -1
#セットアップ完了