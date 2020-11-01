try:
  Library_MotionSpeed
except NameError:
  Library_MotionSpeed = 100
Library_MotionNumberFlag = ${モーションを再生する}
try:
    if(Library_BeforeMotionNumber!=Library_MotionNumberFlag):
        if(Library_BeforeMotionNumber == 70 or Library_BeforeMotionNumber == 73):
            Library_MotionStart(Library_BeforeMotionNumber,Library_MotionSpeed,1)
except NameError:
    None
Library_MotionStart(${モーションを再生する},Library_MotionSpeed,0)
Library_BeforeMotionNumber = ${モーションを再生する}
Library_MotionNumberFlag = -1
if(Library_BeforeMotionNumber==70 or Library_BeforeMotionNumber==73):
    def ContinueEnd(): #歩行終了モーション
        wait_ms(50)
        if(Library_MotionNumberFlag == -1):
          if(Library_BeforeMotionNumber == 70 or Library_BeforeMotionNumber == 73):
            Library_MotionStart(Library_BeforeMotionNumber,Library_MotionSpeed,1)
    #連続歩行終了確認スレッドを実行する
    _thread.start_new_thread(ContinueEnd, ())
