/*
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
*/

#include "huffmanAlgo.h"

void comprsdHex(FILE * cbf , FILE * cf){
  // int c, i, cnt=0;
  // char tmp[MAX_CODE_LEN] ={'x'}; // initialize the array to none hex symbol
 char c[5];
  while(( c[0] = fgetc(cbf)) != EOF )
  {
    if( ( c[1] = fgetc(cbf) ) != EOF){
    }else{
      c[1] = c[2] = c[3] =0;
    }
    if( (c[2] = fgetc(cbf) ) != EOF){
    }else{
       c[2] = c[3] =0;
    }
    if( ( c[3] = fgetc(cbf) ) != EOF){
    }else{
      c[3] =0;
    }
    c[4] = '\0';
    if( !strcmp(c,"0000") ){
      fprintf(cf, "%c", '0');
    }else if( !strcmp(c,"0001") ){
      fprintf(cf, "%c", '1');
    }else if( !strcmp(c ,"0010") ){
      fprintf(cf, "%c", '2');
    }else if( !strcmp(c ,"0011") ){
      fprintf(cf, "%c", '3');
    }else if( !strcmp(c ,"0100") ){
      fprintf(cf, "%c", '4');
    }else if( !strcmp(c ,"0101") ){
      fprintf(cf, "%c", '5');
    }else if( !strcmp(c ,"0110") ){
      fprintf(cf, "%c", '6');
    }else if( !strcmp(c ,"0111") ){
      fprintf(cf, "%c", '7');
    }else if( !strcmp(c ,"1000") ){
      fprintf(cf, "%c", '8');
    }else if( !strcmp(c ,"1001") ){
      fprintf(cf, "%c", '9');
    }else if( !strcmp(c ,"1010") ){
      fprintf(cf, "%c", 'A');
    }else if( !strcmp(c ,"1011") ){
      fprintf(cf, "%c", 'B');
    }else if( !strcmp(c ,"1100") ){
      fprintf(cf, "%c", 'C');
    }else if( !strcmp(c ,"1101") ){
      fprintf(cf, "%c", 'D');
    }else if( !strcmp(c ,"1110") ){
      fprintf(cf, "%c", 'E');
    }else if( !strcmp(c ,"1111") ){
      fprintf(cf, "%c", 'F');
    }else{

    }
  }
}
