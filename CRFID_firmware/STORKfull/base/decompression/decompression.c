/*
  Wisp side decoding algorithm
  @author: Amjad Yousef Majid
*/

#include "decompression.h"
#include "codeTable.h"
#include "msp430fr5969.h"
/*
 * TODO Wisent must first unlock the decompression function
 * which will lock itself at the end of data decompressoin
*/

unsigned int * WP1 = (unsigned int *) 0x18b0;		// Write
unsigned int * WP2 = (unsigned int *) 0x18b2;
unsigned char MWP = 0 ;

unsigned int * RP1 = (unsigned int *) 0x18b4;		// Read
unsigned int * RP2 = (unsigned int *) 0x18b6;
unsigned char MRP = 0 ;

unsigned int  * HBuf1 = (unsigned int *) 0x18b8; 	// Buffer
unsigned int  * HBuf2 = (unsigned int *) 0x18ba;
unsigned int  Buf = 0 ;

unsigned char * WF1 = (unsigned char *) 0x18be;		// write flag
unsigned char * WF2 = (unsigned char *) 0x18bf;
unsigned char MWF = 0;

unsigned char * BP1 = (unsigned char *) 0x18bc;		// Buffer pointer
unsigned char * BP2 = (unsigned char *) 0x18bd;
unsigned char MBP = 0;

unsigned char * MPsP = (unsigned char *) 0x18c0;	// Move pointers

unsigned int *trmi = (unsigned int *) 0x1900;	// decode terminator


static unsigned char *init_flag = ( unsigned char *) 0x18c1; //TODO make sure this is initially 0xff
static unsigned char *call_counter = ( unsigned char *) 0x18c2; //TODO make sure this is initially 0xff
// 0x18c4 is being written to it
unsigned int *func_time = ( unsigned int *) 0x18c6; //TODO make sure this is initially 0xff
unsigned char *int_num = ( unsigned char *) 0x18c8; //TODO make sure this is initially 0xff

unsigned int UFCx =0;
unsigned int UFCy =0;
unsigned int xr =0;
unsigned int xw =0;

void decompression(){
	(*call_counter)++;
	if(*init_flag == 0xff) //TODO this should be enabled
	{
		initialize(); // the content of this function will run only at the very first call (only once)
	}

	checkAndMove();

	unsigned char shVal;

  	while(1){

			shVal = 0;

			if( MBP <= 8 )
			{
				loadByte();
				xr++;
				MBP +=8;
			}

			shVal = decode();
			Buf <<= shVal;
			MBP -= shVal;
			UFCx++;

			if(UFCx > UFCy){
				UFCy++;
				checkAndMove();
				UFCx=0;
				xr=0;
				xw=0;
			}

			if ( ((unsigned int) *WP1+(xw) -  0x6600) >= *trmi ){
				break;
			}
  		}

  	resetting();
  }

void initialize(){
//	TA0CCTL0 |= CCIE ;
//	TA0CTL = MC__CONTINUOUS | TASSEL__SMCLK  | ID__1  | TACLR ;
//	__enable_interrupt();
//	*func_time = 0x00;
//	*int_num = 0x00;

	codeTable();
	*call_counter = 0x00;
	* RP1 = 0x8400;
	* RP2 = 0x8400;

	* WP1 = 0x6600;
	* WP2 = 0x6600;

	*HBuf1= 0x0000;
	*HBuf2= 0x0000;

	* BP1 = 0x00;
	* BP2 = 0x00;

	* WF1 = 0x00;
	* WF2 = 0x00;

	* MPsP= 0x00;

	*init_flag	= 0xAD ; 		//Lock initialize function (Access Denied )
}

void checkAndMove(){
// Safe transaction procedure

	if(*MPsP == 0x00) 		// normal transaction procedure
	{
		*MPsP = 0x01; 		// Moving first set of pointers
		*WP1 += MWP;
		*RP1 += MRP;
			//TODO the following condition should be replaced with a better check to tell if you are in a normal operation or recover from prower interrupt
		if(MWP == 0 && MRP == 0 && Buf == 0 && MBP == 0)  // if wisp recover die during the state-less operation stage
		{
			Buf = *HBuf1;
			MBP = *BP1 ;
			MWF	= *WF1 ;
		}else{
			*HBuf1	= Buf;
			*BP1	= MBP;
			*WF1	= MWF ;
		}

		*MPsP = 0x02; 		// Moving second set of pointers
		*WP2 += MWP;
		*RP2 += MRP;
		*HBuf2= Buf;
		*BP2 = MBP;
		*WF2 = MWF;

		*MPsP= 0x03; 		//reset move pointers
		MWP = 0;
		MRP = 0;
		*MPsP= 0x00; 		// the transition is finished

	}else if(*MPsP == 0x01 )
	{
		*WP1 = *WP2;
		*RP1 = *RP2;
		*HBuf1= *HBuf2;
		*BP1  = *BP2;

		Buf = *HBuf2;
		MBP = *BP2 ;
		MWF	= *WF2 ;

		*MPsP= 0x00; 		// the transition is finished

	}else if(*MPsP == 0x02 )
	{
		*WP2 = *WP1;
		*RP2 = *RP1;
		*HBuf2= *HBuf1;
		*BP2  = *BP1;

		Buf = *HBuf1;
		MBP = *BP1 ;
		MWF	= *WF1 ;

		*MPsP= 0x00; 		// the transition is finished

	}else if(*MPsP == 0x03 )
	{
		Buf = *HBuf1;
		MBP = *BP1 ;
		MWF	= *WF1 ;

		*MPsP= 0x00; 		// the tansition is finished
	}
}

void loadByte(void)
{
	Buf |= *( (unsigned char *)(*RP1+xr)) << (8 - MBP) ;
	MRP++;
}

unsigned char decode()
{
	unsigned char i;
	for(i=0; i <= 16; i++){
		// If there is an exact match between the new byte and a code, output a symbol
		// the extra needed zeros (to form a byte) is added to the MSBs therefore shifting is not required
		if(  ( Buf & (~0 <<( 16- *(LCode+i) ) ) )  == (  ( (unsigned int)*(BCode+i) ) << (16-*(LCode+i) ) ) )
		{
			if(MWF == 1)
			{
				*((unsigned char *)(*WP1+xw) )  |= *(SCode+i) ;
				MWP++;
				MWF = 0;
				xw++;
			}else{
				MWF = 1;
				*((unsigned char *)(*WP1+xw) )  = *(SCode+i)<<4 ;
			}
			break;
		}
	}

	return *(LCode+i) ;
}

void resetting(){
	*init_flag = 0xff ; // Unlock the initiailize function
	DECOMPRESSION_DISABLE;
	//*call_counter = 0X00;
	//	*func_time = TA0R;
}

//#pragma vector=TIMER0_VECTOR
//__interrupt void Timer_A(void)
//{
//	(*int_num)++;
//}














