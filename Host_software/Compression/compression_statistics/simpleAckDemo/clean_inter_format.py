from __future__ import print_function
for line in open("simpleAckDemo.hex"):
	print (line[9:len(line)-2], end="")
