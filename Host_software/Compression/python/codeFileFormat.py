
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


"""The output of this file will be appended to intelFormat.hex file
the DATA (:address 00 data checksum) part of the an output line consists of: 
first the symbol to be send (one hex digit)
second the lenght of the need binary bits in hex format (one hex digit)
third the binary data in hex format  (the binary data is pedded by zeros to make a complete byte)
"""

import math

def convertLine(line):
	
	length = len(line)-3 # the length of the code without the symbol, the : and the newline char 
	line = list(line)
	
	lineFormat(line, length)
	binaryByteBuilder(line, length)
	bin2hex(line)

	line = "".join(line) #convert the list to string
	return line

def lineFormat(line, length):
	""" The output of lineFormat should be <char><length><binary code> """
	line.insert(2, str(length) ) # insert the length of the code in the third position
				     # converting the int to str, so the join function will not complain
	#line.insert(0, '0') # make the first two numbers in :02x hex format 
	#line.insert(3, '0') # 0a:
	line.pop() # remove the newline charactor
	del line[1] # remove the : 

def binaryByteBuilder(line, length):
	"""binaryByteBuilder makes the binary code of length 8"""
	for i in range(8-length): # make the code as one byte of binary data
		line.insert(2,'0') # insert 0's after the symbol and the length <char><length><inserted zeros><binary code>

def bin2hex(line):
	""" bin2hex converts the binary to hexdecimal in :02X format"""
	num =  int( "".join( line[2:] ) , 2) # convert the binary to int
	del line[2:] # remove the binary data
	h = hex(num) # convert the int to hex
	h = h[2:] # remove the 0x
	if len(h) < 2: # ensure that the hex in :02X format
		h= '0'+h
	line.extend( list(h) ) 


def checkSum(line):
	"""checkSum calculate the checksum of a record"""
	checkValue = 0
	lineLength = math.ceil (len(line) / 2 ) # number of bytes per line
	for i in range(0, lineLength):
		checkValue += int("0x" +  line[i*2: (i*2+2)]  , 0 )
	checkValue %=255
	checkValue = "{:02X}".format(checkValue)
	return checkValue


def intelFormat(codeContainer, baseAddress_dec):
	i = 0 
	hexCodeContainer = [] 
	for line in codeContainer:
		address = baseAddress_dec + 2 * i 
		i = i + 1
		address_hex = "{:04x}".format(address)
		line = "".join( ('02', address_hex, '00',line ) )
		checkValue = checkSum(line)
		line = "".join( (':', line, checkValue ) )
		hexCodeContainer.append(line)
	return hexCodeContainer

def print2file(codeContainer, outFile):
	for line in codeContainer:
		print(line, file=outFile) # python 3 style 
	print (":00000001FF" , file=outFile)	# End of File.



def main():
	outFile = open('../output/intelFormat.hex', 'a')
	baseAddress_dec = 6272 # the baseAddress 0x1880 () INFOC 
	codeContainer = []
	for line in open('../dataFiles/code.txt'):
		hexLineData = convertLine(line)
		codeContainer.append(hexLineData)

	hexContainer = intelFormat(codeContainer, baseAddress_dec)
	print2file(hexContainer, outFile )

	

if __name__=="__main__":
	main()
