/*
 * codeTable.c
 *
 *  Created on: Apr 22, 2016
 *      Author: amjad
 */

/*---------------------------------------------------------------
Code container filling
----------------------------------------------------------------*/

unsigned char  * code 	 	 = (unsigned char  *)  0x1880;  	// pointer to the code table ( 32 Bytes + 1 )
unsigned char  * SCode 	 = (unsigned char  *)  0x1850;  	// the symbols of the code table (16 bytes + 1)
unsigned char  * BCode 	 = (unsigned char  *)  0x1860;  	// the binary code part of the code table (16 bytes + 1)
unsigned char  * LCode      = (unsigned char  *)  0x1870;   	// the length of the need binary code 16 bytes  (ends at 1856)


void codeTable(void){
	unsigned char i ;
	for(i = 0 ; i < 16 ; i++){
		*(LCode+i)    = ( (*code) >> 0) & 0x0f;    	// the first 4 digits (length container)
		*(SCode+i) 	  = ( (*code) >> 4) & 0x0f ;    // the second 4 digits (symbol container)

		code ++;
		*(BCode+i) = *code;                   	    // the second byte ( binary code container)
		code++;
	  }
}
