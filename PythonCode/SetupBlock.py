# インポート
import i2c_bus
import re
import math
import machine
import neopixel
import urequests
import _thread
import time

# 変数の定義
Library_ServoDefaultValue = [1000, 630, 300, 600, 240, 600, 1000, 720]
Library_MotionNumberCache = []
Library_TransitionTimeArrayCache = []
Library_SearvoArrayCache = []
Library_ServoBeforeValue = [0] * 8
Library_i2c = i2c_bus.get(i2c_bus.M_BUS)
Library_np = neopixel.NeoPixel(machine.Pin(26), 2)

# グローバル変数の定義
Library_ServoCurrentValue = [0] * 8
Library_CurrentLEDValue = [(0, 0, 0), (0, 0, 0)]
Library_MotionNumberBefore = -1
Library_MotionNumberFlag = -1
Library_ThreadFlag = False
Library_ThreadPlayFlag = False
Library_PlayFlag = False
Library_ServoErrorFlag = False
Library_MotionSpeed = 100

for i in range(8):
    Library_ServoCurrentValue[i] = Library_ServoDefaultValue[i]

# 関数の定義


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
    value = math.floor(degrees * 100 * 226 / 10000) + 0x66
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
        if target != Library_ServoCurrentValue[i]:
            step[i] = (target - Library_ServoCurrentValue[i]) / Library_time
    for n in range(Library_time):
        BeforeTime = time.ticks_ms()
        for m in range(8):
            Library_ServoCurrentValue[m] += step[m]
            Library_servoWrite(m, Library_ServoCurrentValue[m] / 10)
        while(time.ticks_ms() - BeforeTime < 25):
            wait_ms(1)


def Library_GetTime(mode):
    OrganizeList = ["2000", "1", "1", "Sat", "00", "00", "00"]
    try:
        import wifiCfg
        wifiCfg.autoConnect(lcdShow=False)
        req = urequests.request(
            method='GET', url='https://ntp-a1.nict.go.jp/cgi-bin/time', headers={})
        GetData = req.text
        GetData = GetData.replace('  ', ':')
        GetData = GetData.replace(' ', ':')
        TimeList = GetData.split(':')
        OrganizeList = [TimeList[6], TimeList[1], TimeList[2],
                        TimeList[0], TimeList[3], TimeList[4], TimeList[5]]
    except:
        None
    if mode == 0:
        return OrganizeList
    elif OrganizeList[mode - 1]:
        return OrganizeList[mode - 1]
    else:
        return "-1"


def Library_MotionStart(MotionNumber, Mode):
    # 再生モードの確認
    if Mode != 2:
        if Library_MotionNumberBefore == 70 or Library_MotionNumberBefore == 73:
            Mode = 1
        else:
            Mode = 0

    MotionCount = 0

    NeedMotionNumberList = [MotionNumber]
    if MotionNumber in [70, 71, 72, 73]:
        NeedMotionNumberList = [70, 71, 72, 73]

    if MotionNumber not in Library_MotionNumberCache:  # キャッシュ済みか確認
        for Number in NeedMotionNumberList:
            # 歩行モーションデータの読み取り
            ReadData = Library_read8(50 + 860 * Number, 860)

            # モーションデータの切り出し
            MotionDataArray = str(ReadData).split('>')
            TransitionTimeArray = []
            SearvoArray = []

            for i in MotionDataArray:
                if re.match('^MF' + '{:02x}'.format(Number), i):
                    check1 = re.match('(MF....)(....)', i)
                    TransitionTimeArray.append(int(check1.group(2), 16))
                    for n in range(8):
                        check2 = int(i[10 + 4 * n:10 + 4 * n + 4], 16)
                        if check2 >= 0x7fff:
                            check2 = ~(~check2 & 0xffff)
                        else:
                            check2 = check2 & 0xffff
                        SearvoArray.append(check2)
            # 読み込んだデータはキャッシュする
            Library_MotionNumberCache.append(Number)
            Library_TransitionTimeArrayCache.append(TransitionTimeArray)
            Library_SearvoArrayCache.append(SearvoArray)

    CacheNumber = Library_MotionNumberCache.index(MotionNumber)
    # キャッシュから取得する
    TransitionTimeArray = Library_TransitionTimeArrayCache[CacheNumber]
    SearvoArray = Library_SearvoArrayCache[CacheNumber]

    # サーボモータを動かす
    ErrorFlag = False
    LoopTimes = len(TransitionTimeArray)
    while MotionCount != LoopTimes:
        SearvoArrayCheck = []
        for i in range(8):
            count1 = 8 * MotionCount + i
            SearvoArrayCheck.append(SearvoArray[count1])

        MotionFlag = True
        if MotionNumber in [70, 71, 72, 73]:  # 連続歩行確認
            if Mode == 1:  # 中間のみ再生
                if MotionCount >= LoopTimes - 2:  # 歩行最後の2モーションカット
                    MotionCount += 1
                    MotionFlag = False
                elif MotionCount <= 1:  # 歩行最初の2モーションカット
                    MotionCount += 1
                    MotionFlag = False
            if Mode == 2:  # 連続歩行を終了する(最後のモーションのみ再生)
                if MotionCount < LoopTimes - 2:
                    MotionCount += 1
                    MotionFlag = False
            else:  # 歩行最後の2モーションカット
                if MotionCount >= LoopTimes - 2:  # 歩行最後の2モーションカット
                    MotionCount += 1
                    MotionFlag = False

        if MotionFlag:
            if Library_ServoBeforeValue == SearvoArrayCheck:  # 同じサーボ角を繰り返す場合、動作スキップする
                MotionCount += 1
            else:
                MotionCountBefore = MotionCount
                Library_setAngle(
                    SearvoArrayCheck, TransitionTimeArray[MotionCount] / (Library_MotionSpeed / 100))
                MotionCount += 1
        for i in range(8):
            Library_ServoBeforeValue[i] = SearvoArrayCheck[i]


def Library_ContinueEnd():  # 連続歩行終了を確認
    global Library_MotionNumberBefore, Library_MotionNumberFlag, Library_ThreadFlag, Library_ThreadPlayFlag
    Library_ThreadFlag = True
    wait_ms(25)
    if Library_PlayFlag == False:
        if Library_MotionNumberBefore in [70, 71, 72, 73]:
            Library_ThreadPlayFlag = True
            Library_MotionStart(Library_MotionNumberBefore, 2)
            Library_ThreadPlayFlag = False
    Library_ThreadFlag = False
    Library_MotionNumberBefore = -1
    Library_MotionNumberFlag = -1


def Library_SetLED(mode, R, G, B):
    global Library_CurrentLEDValue
    if mode == 1:
        Library_CurrentLEDValue[0] = list(map(int, [G, R, B]))
    elif mode == 2:
        Library_CurrentLEDValue[1] = list(map(int, [G, R, B]))
    else:
        Library_CurrentLEDValue[0] = list(map(int, [G, R, B]))
        Library_CurrentLEDValue[1] = list(map(int, [G, R, B]))
    for x in range(2):
        for y in range(3):
            if Library_CurrentLEDValue[x][y] < 0:
                Library_CurrentLEDValue[x][y] = 0
            if Library_CurrentLEDValue[x][y] > 255:
                Library_CurrentLEDValue[x][y] = 255
    Library_np[0] = Library_CurrentLEDValue[0]
    Library_np[1] = Library_CurrentLEDValue[1]
    Library_np.write()


def Library_SetSpeed(speed):
    global Library_MotionSpeed
    if speed < 10:
        speed = 10
    elif speed > 250:
        speed = 250
    Library_MotionSpeed = speed


def Library_PlayMotion(MotionNumber):
    global Library_MotionNumberBefore, Library_MotionNumberFlag, Library_PlayFlag
    if Library_ServoErrorFlag:
        Library_ServoSetUp()
    Library_MotionNumberFlag = MotionNumber
    Check1 = 0
    Check2 = 0
    if Library_MotionNumberBefore == 70 or Library_MotionNumberBefore == 73:
        Check1 = 1
    elif Library_MotionNumberBefore == 71 or Library_MotionNumberBefore == 72:
        Check1 = 2
    if Library_MotionNumberFlag == 70 or Library_MotionNumberFlag == 73:
        Check2 = 1
    elif Library_MotionNumberFlag == 71 or Library_MotionNumberFlag == 72:
        Check2 = 2

    if Check1 == 0 or Check1 != Check2:
        # 連続歩行終了確認スレッドが終了するまで待つ
        while(Library_ThreadFlag):
            wait_ms(1)
    Library_PlayFlag = True
    Library_MotionStart(MotionNumber, 0)
    Library_PlayFlag = False
    Library_MotionNumberBefore = MotionNumber
    if MotionNumber in [70, 71, 72, 73]:
        # 連続歩行終了確認スレッドを実行する
        _thread.start_new_thread(Library_ContinueEnd, ())
        while(Library_ThreadFlag == False):
            wait_ms(1)


def Library_SetServo(ServoAngleArray, Time):
    global Library_PlayFlag
    if Library_ServoErrorFlag:
        Library_ServoSetUp()
    # 連続歩行終了確認スレッドが終了するまで待つ
    while(Library_ThreadFlag):
        wait_ms(1)
    Library_PlayFlag = True
    if Time < 25:
        Time = 25  # 25msecが限界
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
    except:
        Library_ServoErrorFlag = True


# 初期化
Library_ServoSetUp()
# セットアップ完了
