/*
  Wisp side decompression algorithm
  @author: Amjad Yousef Majid
*/

#include <stdint.h>

#ifndef DECOMPRESSION_DECOMPRESSION_H_
#define DECOMPRESSION_DECOMPRESSION_H_

#define DECOMPRESSION_IS_FINISHED (*( unsigned char *) 0x1950 == 0xad )
#define DECOMPRESSION_DISABLE (*( unsigned char *) 0x1950 = 0xad )
#define DECOMPRESSION_ENABLE (*( unsigned char *) 0x1950 = 0xff )

extern unsigned int * RP1;
extern unsigned int * RP2;
extern unsigned int * WP1;
extern unsigned int * WP2;
extern unsigned char BP;
extern unsigned char * MPsP;
extern unsigned int  Buf ;

void decompression(void);
void initialize(void);
void checkAndMove(void);
void loadByte(void);
unsigned char decode(void);
void resetting(void);
#endif /* DECOMPRESSION */
