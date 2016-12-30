/*
  Wisp side deconding algorithm
  @author: Amjad Yousef Majid
*/

#include <stdint.h>

#ifndef DECOMPRESSION_DECOMPRESSION_H_
#define DECOMPRESSION_DECOMPRESSION_H_


extern unsigned char BP;
extern unsigned int  Buf ;

void decompression(void);
void initialize(void);
void checkAndMove(void);
void loadByte(void);
unsigned char decode(void);
void resetting(void);
#endif /* DECOMPRESSION */
