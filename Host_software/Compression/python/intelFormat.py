
#  Copyright (c) 2016,                                                                              #
#  Author: Amjad Yousef Majid                                                                       #
#  Date: 16/06/2016                                                                                 #
#  All rights reserved.                                                                             #
#                                                                                                   #
# Redistribution and use in source and binary forms, with or without                                #
# modification, are permitted provided that the following conditions are met:                       #
#     * Redistributions of source code must retain the above copyright                              #
#       notice, this list of conditions and the following disclaimer.                               #
#     * Redistributions in binary form must reproduce the above copyright                           #
#       notice, this list of conditions and the following disclaimer in the                         #
#       documentation and/or other materials provided with the distribution.                        #
#     * Neither the name of the <organization> nor the                                              #
#       names of its contributors may be used to endorse or promote products                        #
#       derived from this software without specific prior written permission.                       #
#                                                                                                   #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND                   #
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED                     #
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE                            #
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY                                #
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES                        #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;                      #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND                       #
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT                        #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS                     #
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.                                      #

'''
	This script convert a random hex file to an hex file in inetl format 
	which is < : length address 00 data checksum
	The maximum length of the output line is 32 bytes, because this is 
	the max allowed length by a BlockWrite

	This script is part of Wisent++ project

	Date 23/03/2016
	Author Amjad Yousef Majid

'''
import math
import codeFileFormat

def writeLine( baseAddress_dec, line, outFile ):
		'''writeLine writes a line to the output file and return the base address for the next line'''
		# if the number of hex digits is odd, add a zero before the last one (complete the last byte)		
		if len(line) % 2 != 0: 
			line = line[:]+list('f') #TODO here I'm adding f at the end if I have half a byte. This will change the checksum
		if (len(line) / 2 ) % 2 != 0 :
			line = line+list('00')
		lineLength =  int(len(line) / 2 ) # number of bytes per line
		intelDelimiter = "00"
		
		# hexdecimal values
		address = "{:04X}".format(baseAddress_dec)
		length = "{:02X}".format(lineLength)

		record = "".join(  ( str(length),str(address) , intelDelimiter, "".join(line) ) ) 

		# get the checksum of the value
		checkValue = checkSum(record)
		record = "".join( ( ":" , record , checkValue) )
		print(record , file=outFile)

		baseAddress_dec = baseAddress_dec  + lineLength # the baseAddress for the next line
		return baseAddress_dec # retrun the new base



def openInFile():
	''' openInFile prompt the user for input hex file'''
	#inFile = input("Please enter file name: ")
	inFile = '../dataFiles/CompressedFile.hex'  # NEEDS TO BE REMOVED !!!!!!!!!!!!!!!!!!!!!
	try:
		fh = open(inFile, 'r')						
		return fh
	except IOError:
		print("Cannot open " , inFile)


def openOutFile():
	''' openOutFile specifies the output file '''
	return open("../output/intelFormat.hex", 'w')

def checkSum(line):
	checkValue = 0
	lineLength = math.ceil (len(line) / 2 ) # number of bytes per line
	for i in range(0, lineLength):
		checkValue += int("0x" +  line[i*2: (i*2+2)]  , 0 )
	checkValue %=255
	checkValue = "{:02X}".format(checkValue)
	return checkValue

def byteCounter():
	totNum=0
	for line in open("../dataFiles/dump.hex"): # The dump.hex file has only the data that is about to be compressed
		totNum += len(line)-1
	totNumHex =  hex( int(math.ceil(totNum / 2.0)) )
	totNumHex = totNumHex[4:6]+totNumHex[2:4] # workaround the little endian format of writing to memory and remove the 0x
	return list(totNumHex)	

def main():

	i = 0
	baseAddress_hex = "6400" 
	baseAddress_dec = int("0x" + baseAddress_hex , 0) 
	hexInLine = 32 *  2.0 # max number of hex digit in line
	line = [];   # line container
	fh = openInFile()
	outFile = openOutFile()

	
	c = fh.read(1)

	while c :
		if c =='\n': # if there is a newline skip it
			c = fh.read(1)
			continue

		line.append(c)
		
		i +=1
		if i % hexInLine == 0:
			baseAddress_dec = writeLine( baseAddress_dec, line, outFile ) 
			line=[]

		c = fh.read(1)


	if len(line) > 0 :
		baseAddress_dec = writeLine( baseAddress_dec, line, outFile ) 
		line=[]
	line = byteCounter()
	baseAddress_dec = writeLine( int("0x1900", 0), line, outFile ) 
	line=[]


if __name__ == '__main__':
	main()
	codeFileFormat.main()
