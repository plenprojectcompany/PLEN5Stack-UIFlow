#インポート
import i2c_bus
import re
import math
import machine, neopixel
import urequests
import _thread
import time

#変数の定義
Library_ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
Library_MotionNumberCache = []
Library_TransitionTimeArrayCache = []
Library_SearvoArrayCache = []
Library_CurrentLEDValue = [(0,0,0),(0,0,0)]
Library_ServoCurrentValue = [0] * 8
Library_ServoBeforeValue = [0] * 8
Library_i2c = i2c_bus.get(i2c_bus.M_BUS)
Library_np = neopixel.NeoPixel(machine.Pin(26), 2)

#グローバル変数の定義
global Library_MotionNumberBefore
Library_MotionNumberBefore = -1
global Library_MotionNumberFlag
Library_MotionNumberFlag = -1
global Library_ThreadFlag
Library_ThreadFlag = False
global Library_ThreadPlayFlag
Library_ThreadPlayFlag = False
global Library_PlayFlag
Library_PlayFlag = False
global Library_MotionSpeed
Library_MotionSpeed = 100

for i in range(8):
  Library_ServoCurrentValue[i] = Library_ServoDefaultValue[i]

#関数の定義
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

def Library_GetTime(mode):
    try:
      remoteInit()
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

def Library_MotionStart(MotionNumber,Speed,Mode):
    #再生モードの確認
    global Library_MotionNumberBefore
    if(Mode!=2):
        if(Library_MotionNumberBefore==70 or Library_MotionNumberBefore==73):
            Mode=1
        else:
            Mode=0

    MotionCount = 0

    if(MotionNumber==70 or MotionNumber==71 or MotionNumber==72 or MotionNumber==73):
      #連続歩行用にキャッシュしておく
      if(MotionNumber in Library_MotionNumberCache): #キャッシュされているか確認
          None
      else:
          for Number in range(4):
              #h歩行モーションデータの読み取り
              ReadByteFrom = 50 + 860 * (70 + Number)
              _data = bytearray(2)
              _data[0] = ReadByteFrom >> 8
              _data[1] = ReadByteFrom & 0xFF
              Library_i2c.writeto(0x56, _data)
              ReadData = Library_i2c.readfrom(0x56, 860)

              #モーションデータの切り出し
              MotionDataArray = str(ReadData).split('>')
              TransitionTimeArray = []
              SearvoArray = []

              for i in MotionDataArray:
                  if(re.match('^MF' + '{:02x}'.format(70 + Number),i)):
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
              Library_MotionNumberCache.append(70 + Number)
              Library_TransitionTimeArrayCache.append(TransitionTimeArray)
              Library_SearvoArrayCache.append(SearvoArray)

    if(MotionNumber in Library_MotionNumberCache): #キャッシュされているか確認
        CacheNumber = Library_MotionNumberCache.index(MotionNumber)
        #キャッシュから取得する
        TransitionTimeArray = Library_TransitionTimeArrayCache[CacheNumber]
        SearvoArray = Library_SearvoArrayCache[CacheNumber]
    else:
        #モーションデータの読み取り
        ReadByteFrom = 50 + 860 * MotionNumber
        _data = bytearray(2)
        _data[0] = ReadByteFrom >> 8
        _data[1] = ReadByteFrom & 0xFF
        Library_i2c.writeto(0x56, _data)
        ReadData = Library_i2c.readfrom(0x56, 860)

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
        Library_MotionNumberCache.append(MotionNumber)
        Library_TransitionTimeArrayCache.append(TransitionTimeArray)
        Library_SearvoArrayCache.append(SearvoArray)

    #サーボモーターを動かす
    ErrorFlag = False
    LoopTimes = len(TransitionTimeArray)
    while MotionCount != LoopTimes:
      SearvoArrayCheck = []
      for i in range(8):
        count1 = 8 * MotionCount + i
        SearvoArrayCheck.append(SearvoArray[count1])

      MotionFlag=True
      if(MotionNumber==70 or MotionNumber==71 or MotionNumber==72 or MotionNumber==73): #連続歩行確認
        if(Mode==1): #中間のみ再生
            if(MotionCount>=LoopTimes-2): #歩行最後の2モーションカット
              MotionCount+=1
              MotionFlag=False
            elif(MotionCount<=1): #歩行最初の2モーションカット
              MotionCount+=1
              MotionFlag=False
        if(Mode==2): #連続歩行を終了する(最後のモーションのみ再生)
          if(MotionCount<LoopTimes-2):
            MotionCount+=1
            MotionFlag=False
        else: #歩行最後の2モーションカット
          if(MotionCount>=LoopTimes-2): #歩行最後の2モーションカット
            MotionCount+=1
            MotionFlag=False

      if(MotionFlag):
        if(Library_ServoBeforeValue == SearvoArrayCheck): #同じサーボ角を繰り返す場合、動作スキップする
          MotionCount+=1
        else:
          MotionCountBefore = MotionCount
          Library_setAngle(SearvoArrayCheck,TransitionTimeArray[MotionCount]/(Speed / 100))
          MotionCount += 1
      for i in range(8):
        Library_ServoBeforeValue[i] = SearvoArrayCheck[i]

def Library_ContinueEnd(): #連続歩行終了を確認
    global Library_MotionNumberBefore
    global Library_MotionNumberFlag
    global Library_ThreadFlag
    global Library_ThreadPlayFlag
    global Library_PlayFlag
    global Library_MotionSpeed
    Library_ThreadFlag = True
    wait_ms(25)
    if(Library_PlayFlag == False):
        if(Library_MotionNumberBefore == 70 or Library_MotionNumberBefore == 71 or Library_MotionNumberBefore == 72 or Library_MotionNumberBefore == 73):
            Library_ThreadPlayFlag = True
            Library_MotionStart(Library_MotionNumberBefore,Library_MotionSpeed,2)
            Library_ThreadPlayFlag = False
    Library_ThreadFlag = False
    Library_MotionNumberBefore = -1
    Library_MotionNumberFlag = -1

def Library_PlayMotion(MotionNumber):
    global Library_MotionNumberBefore
    global Library_MotionNumberFlag
    global Library_ThreadFlag
    global Library_ThreadPlayFlag
    global Library_PlayFlag
    global Library_MotionSpeed
    Library_MotionNumberFlag = MotionNumber
    Check1 = 0
    Check2 = 0
    if(Library_MotionNumberBefore==70 or Library_MotionNumberBefore==73):
        Check1 = 1
    elif(Library_MotionNumberBefore==71 or Library_MotionNumberBefore==72):
        Check1 = 2
    if(Library_MotionNumberFlag==70 or Library_MotionNumberFlag==73):
        Check2 = 1
    elif(Library_MotionNumberFlag==71 or Library_MotionNumberFlag==72):
        Check2 = 2

    if(Check1 == 0 or Check1 != Check2):
        #連続歩行終了確認スレッドが終了するまで待つ
        while(Library_ThreadFlag):
            wait_ms(1)
    while(Library_ThreadPlayFlag):
            wait_ms(1)
    Library_PlayFlag = True
    Library_MotionStart(MotionNumber,Library_MotionSpeed,0)
    Library_PlayFlag = False
    Library_MotionNumberBefore = MotionNumber
    if(MotionNumber==70 or MotionNumber==71 or MotionNumber==72 or MotionNumber==73):
        #連続歩行終了確認スレッドを実行する
        _thread.start_new_thread(Library_ContinueEnd, ())
        while(Library_ThreadFlag==False):
            wait_ms(1)

def Library_SetServo(ServoAngleArray,Time):
    global Library_MotionNumberBefore
    global Library_MotionNumberFlag
    global Library_ThreadFlag
    global Library_PlayFlag
    global Library_MotionSpeed
    #連続歩行終了確認スレッドが終了するまで待つ
    while(Library_ThreadFlag):
        wait_ms(1)
    Library_PlayFlag = True
    if(Time<25):
        Time=25 #25msecが限界
    Library_setAngle(ServoAngleArray,Time)
    Library_PlayFlag = False

#初期化
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
#セットアップ完了
