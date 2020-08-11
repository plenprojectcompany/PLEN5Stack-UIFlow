CurrentLEDValue[0] = list(map(int,[${G}, ${R}, ${B}]))
CurrentLEDValue[1] = list(map(int,[${G}, ${R}, ${B}]))
np[0] = CurrentLEDValue[0]
np[1] = CurrentLEDValue[1]
np.write()
