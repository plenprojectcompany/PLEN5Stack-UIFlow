Library_MotionNumberFlag = -2
try:
    if(Library_BeforeMotionNumber == 70 or Library_BeforeMotionNumber == 73):
        Library_MotionStart(Library_BeforeMotionNumber,Library_MotionSpeed,1)
except NameError:
    None
ServoAngleArray = [${Angle0}*10,${Angle1}*10,${Angle2}*-10,${Angle3}*10,${Angle4}*-10,${Angle5}*-10,${Angle6}*10,${Angle7}*-10]
Library_setAngle(ServoAngleArray,${Time})
Library_BeforeMotionNumber = -2
