
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

from __future__ import print_function
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", help="r: remove the new lines charaters")
parser.add_argument("-i", help="r: remove intel formatting")
parser.add_argument("-w", default="../dataFiles/dump.hex", help="output file name")
parser.add_argument("-r", default="../dataFiles/run-wireless.hex", help="input file name")


def main():
	args = parser.parse_args()

	ofile = args.w
	ifile = args.r

	# remove intel formatting
	if args.i == 'r' and args.n == 'r':
		remove_intel_format_newline(ifile, ofile)
	elif args.i == 'r':
		remove_intel_format(ifile, ofile)
	elif args.n == 'r':
		remove_newline(ifile, ofile)


def remove_intel_format(ifile, ofile):
	in_file = open(ifile, 'r')
	out_file = open(ofile, 'w')
	for line in in_file:
		line = line[9:-3]
		print (line, file=out_file)

def remove_intel_format_newline(ifile, ofile):
	in_file = open(ifile, 'r')
	out_file = open(ofile, 'w')
	for line in in_file:
		line = line[9:-3]
		print (line, file=out_file, end="")

def remove_newline(ifile, ofile,):
	in_file = open(ifile, 'r')
	out_file = open(ofile, 'w')
	for line in in_file:
		line = line[:-1]
		print (line, file=out_file ,end="" )

if __name__=='__main__':
	main()
