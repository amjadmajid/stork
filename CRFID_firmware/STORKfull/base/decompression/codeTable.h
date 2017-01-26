/*
 * codeTable.h
 *
 *  Created on: Apr 22, 2016
 *      Author: Amjad Yousef Majid
 */

#ifndef DECOMPRESSION_CODETABLE_H_
#define DECOMPRESSION_CODETABLE_H_

/*---------------------------------------------------------------
code containers  pointers
----------------------------------------------------------------*/
extern unsigned char * code ;
extern unsigned char * SCode ;
extern unsigned char * BCode ;
extern unsigned char * LCode  ;

void codeTable(void);

#endif /* DECOMPRESSION_CODETABLE_H_ */
