try:
  Library_MotionSpeed
except NameError:
  Library_MotionSpeed = 100
Library_MotionNumberFlag = ${モーションを再生する}
if(Library_BeforeMotionNumber!=Library_MotionNumberFlag):
    if(Library_BeforeMotionNumber == 70 or Library_BeforeMotionNumber == 73):
        Library_MotionStart(Library_BeforeMotionNumber,Library_MotionSpeed,1)
Library_MotionStart(${モーションを再生する},Library_MotionSpeed,0)
Library_BeforeMotionNumber = ${モーションを再生する}
Library_MotionNumberFlag = -1
if(Library_BeforeMotionNumber==70 or Library_BeforeMotionNumber==73):
    #連続歩行終了確認スレッドを実行する
    _thread.start_new_thread(ContinueEnd, ())
