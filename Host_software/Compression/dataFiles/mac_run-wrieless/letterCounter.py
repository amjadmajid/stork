import math
totNum=0
for line in open("dump.hex"):
	totNum += len(line)-1
print math.ceil(totNum / 2.0), " = ",  hex( int(math.ceil(totNum / 2.0)) )
