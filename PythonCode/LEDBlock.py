Library_CurrentLEDValue[0] = list(map(int,[${G}, ${R}, ${B}]))
Library_CurrentLEDValue[1] = list(map(int,[${G}, ${R}, ${B}]))
Library_np[0] = Library_CurrentLEDValue[0]
Library_np[1] = Library_CurrentLEDValue[1]
Library_np.write()
