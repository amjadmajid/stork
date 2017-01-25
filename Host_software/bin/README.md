#  Copyright (c) 2016,                                                                              #
# Author(s): Henko Aantjes,                                                                         #                 
# Date: 28/07/2016                                                                                  #

run the files: ./filename

names tell you which python they execute, see readme in sllurp for more info

exception:
file w23_1 reprograms wisp ID 0301 with ccs1.hex, which turns led 1 on
file w23_2 reprograms wisp ID 0301 with ccs2.hex, which turns led 2 on
stork can be used as: ./stork -n 10 -s 2 -P 4 -f ihex/ccs1.hex -w 0x0301 -M WISP5 -l w301_1log.txt 192.168.10.5
that will make it the same as w23_1
