from __future__ import print_function
for line in open("accelDemo.hex"):
	print (line[9:len(line)-2], end="")
