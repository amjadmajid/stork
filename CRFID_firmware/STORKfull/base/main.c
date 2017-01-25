/* Author: Henko Aantjes,            
 * Date: 28/07/2016
*/

#include "wisp-base.h"

//#define BSL_VIRTUAL_ID   0x1900
#include "decompression/decompression.h"

#define LOC_BSL_STATE 		0x1920
#define LOC_BSL_ID 			0x1910
#define LOC_LAST_ACK0_L_CS	0x1930
#define LOC_LAST_ACK1_ADDR	0x1932
#define LOC_CONSISTENT_PAR  0x1934
#define LOC_CONSISTENT_PAR2 0x1936
#define LOC_ADDRESS_LIST_TO_READ 0x1938

#define BSL_STATE   		(* (uint16_t *) (LOC_BSL_STATE))
#define BSL_ID				(* (uint16_t *) (LOC_BSL_ID))
#define LAST_ACK0_L_CS   	(* (uint16_t *) (LOC_LAST_ACK0_L_CS))
#define LAST_ACK1_ADDR		(* (uint16_t *) (LOC_LAST_ACK1_ADDR))
#define ADDRESS_TO_READ		(* (uint16_t *) (LOC_CONSISTENT_PAR))
#define ADDRESS_NR_TO_READ	(* (uint16_t *) (LOC_CONSISTENT_PAR2))
#define ADDRESS_LIST_TO_READ (* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ))
//(* (uint16_t *) (BSL_STATE)) can be boot(b007), bios(b015), eavedropping/sniffing(ea4e) or empty(0)
#define HEADERLENGTH	 2

#define POWERMEASUREMENTS  0
#define DECOMPRESSIONTIMETEST 1


WISP_dataStructInterface_t wispData;
//char crcnr=0;

/**
 * This function is called by WISP FW after a successful ACK reply
 *
 */
void my_ackCallback (void) {
	asm(" NOP");
}

/**
 * This function is called by WISP FW after a successful read command
 *  reception
 *
 */
void my_readCallback (void) {
//	uint16_t * readBuff16_t;
//		readBuff16_t = (uint16_t *) wispData.readBufPtr;
//	 if(ADDRESS_NR_TO_READ< 12){
//		ADDRESS_TO_READ = (* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ + ADDRESS_NR_TO_READ));
//		readBuff16_t[0] = (* (uint16_t *) (ADDRESS_TO_READ+0));
//		readBuff16_t[1] = (* (uint16_t *) (ADDRESS_TO_READ+2));
//		readBuff16_t[2] = (* (uint16_t *) (ADDRESS_TO_READ+4));
//		readBuff16_t[3] = (* (uint16_t *) (ADDRESS_TO_READ+6));
//		readBuff16_t[4] = (* (uint16_t *) (ADDRESS_TO_READ+8));
//		readBuff16_t[5] = (* (uint16_t *) (ADDRESS_TO_READ+10));
//		readBuff16_t[6] = (* (uint16_t *) (ADDRESS_TO_READ+12));
//		readBuff16_t[7] = (* (uint16_t *) (ADDRESS_TO_READ+14));
//		readBuff16_t[8] = (* (uint16_t *) (ADDRESS_TO_READ+16));
//		readBuff16_t[9] = (* (uint16_t *) (ADDRESS_TO_READ+18));
//		readBuff16_t[10] = (* (uint16_t *) (ADDRESS_TO_READ+20));
//		readBuff16_t[11] = (* (uint16_t *) (ADDRESS_TO_READ+22));
//		readBuff16_t[12] = (* (uint16_t *) (ADDRESS_TO_READ+24));
//		readBuff16_t[13] = (* (uint16_t *) (ADDRESS_TO_READ+26));
//		readBuff16_t[14] = (* (uint16_t *) (ADDRESS_TO_READ+28));
//		readBuff16_t[15] = ADDRESS_TO_READ;
//		ADDRESS_NR_TO_READ = ADDRESS_NR_TO_READ + 2;
//	}
//	else if(ADDRESS_TO_READ < 0xFF00){
//		readBuff16_t[0] = (* (uint16_t *) (ADDRESS_TO_READ+0));
//		readBuff16_t[1] = (* (uint16_t *) (ADDRESS_TO_READ+2));
//		readBuff16_t[2] = (* (uint16_t *) (ADDRESS_TO_READ+4));
//		readBuff16_t[3] = (* (uint16_t *) (ADDRESS_TO_READ+6));
//		readBuff16_t[4] = (* (uint16_t *) (ADDRESS_TO_READ+8));
//		readBuff16_t[5] = (* (uint16_t *) (ADDRESS_TO_READ+10));
//		readBuff16_t[6] = (* (uint16_t *) (ADDRESS_TO_READ+12));
//		readBuff16_t[7] = (* (uint16_t *) (ADDRESS_TO_READ+14));
//		readBuff16_t[8] = (* (uint16_t *) (ADDRESS_TO_READ+16));
//		readBuff16_t[9] = (* (uint16_t *) (ADDRESS_TO_READ+18));
//		readBuff16_t[10] = (* (uint16_t *) (ADDRESS_TO_READ+20));
//		readBuff16_t[11] = (* (uint16_t *) (ADDRESS_TO_READ+22));
//		readBuff16_t[12] = (* (uint16_t *) (ADDRESS_TO_READ+24));
//		readBuff16_t[13] = (* (uint16_t *) (ADDRESS_TO_READ+26));
//		readBuff16_t[14] = (* (uint16_t *) (ADDRESS_TO_READ+28));
//		readBuff16_t[15] = ADDRESS_TO_READ;
//		ADDRESS_TO_READ = ADDRESS_TO_READ + 30;
//	}
//	else
//	{
//		readBuff16_t[15] = ADDRESS_TO_READ;
//	}
}

/**
 * This function is called by WISP FW after a successful write command
 *  reception
 *
 */
void my_writeCallback (void) {
	/*(* (uint16_t *)(wispData.writePtr+0x6400)) = wispData.writeBufPtr[0];
}*/

	// Get data descriptor.
	uint8_t hi = (wispData.writeBufPtr[0] >> 8)  & 0xFF;
	uint8_t lo = (wispData.writeBufPtr[0])  & 0xFF;

	// Write bootloader password if correct command is given.
	if (wispData.writeBufPtr[0] ==0xb105) {
		BSL_STATE = 0xB105; // set password
		wispData.epcBuf[10]= (BSL_STATE >> 8)& 0xFF; // bios (hi)
		wispData.epcBuf[11]= BSL_STATE & 0xFF; // bios (lo)
		rfid.isEavesDropping = 0; // disable eavesdropp
		DECOMPRESSION_ENABLE;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = hi;
		wispData.readBufPtr[1]  = lo;
		wispData.readBufPtr[2]  = 0x00;
		wispData.readBufPtr[3]  = 0x00;
		wispData.readBufPtr[4]  = 0x00;
		if(POWERMEASUREMENTS)
			P3OUT |=  BIT4; // set aux on
	} else if (wispData.writeBufPtr[0] ==0xB007) {
		BSL_STATE = 0xB007;
		// POR.
		PMMCTL0 |= PMMSWPOR;
	} else if (wispData.writeBufPtr[0] == 0xea41){ // command stop eavesdropping
		rfid.isEavesDropping = 1;
		BSL_STATE = 0xea4e;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = hi;
		wispData.readBufPtr[1]  = lo;
		wispData.epcBuf[10]= (BSL_STATE >> 8)& 0xFF; // bios (hi)
		wispData.epcBuf[11]= BSL_STATE & 0xFF; // bios (lo)
	} else if (wispData.writeBufPtr[0] == 0xdecd){ // command dec0-mpress
		BSL_STATE = 0xdecd;
		if(! DECOMPRESSION_IS_FINISHED){
			PMMCTL0 |= PMMSWPOR;
//			if(DECOMPRESSIONTIMETEST)
//				P3OUT |=  BIT4;
//			decompression();
//			if(DECOMPRESSIONTIMETEST)
//				P3OUT &=  ~BIT4;
		}
		BSL_STATE = 0xb105;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = 0xde;
		wispData.readBufPtr[1]  = 0xcd;
		wispData.readBufPtr[2]  = 0x00;
		wispData.readBufPtr[3]  = 0x00;


	}
}

/**
 * This function is hidden within the process time of the wisp BEFORE responding to the reader!
 * While the maximum delayed response time is 20 ms, the WISP lives for ~14 ms per power cycle.
 * Furthermore, the bigger this function is, the smaller the time window becomes (i.e. less bwr/sec).
 */
void my_blockWriteCallback  (void) {
	// get the different parts of the message:
	// [ 3bit resultpos | 5bit length | 8bit checksum | 16bit address | X*16bit data ]
	uint8_t result_position = (wispData.blockWriteBufPtr[0] & 0xE000)>>(13-2); // result already multiplied by 4, because each result has a length of 4 bytes
	uint8_t nr_of_data_words= (wispData.blockWriteBufPtr[0] >> 8)  & 0x1F;
	uint8_t checksum		=  wispData.blockWriteBufPtr[0] & 0x00FF;
	uint16_t address   		= wispData.blockWriteBufPtr[1];
	// initialise parameters
	uint8_t offset     		= 0x00;
	uint8_t calcsum    		= 0x00;
	uint16_t crc = 0xFFFF;
	uint16_t * readBuff16_t;
	readBuff16_t = (uint16_t *) wispData.readBufPtr;

	if(nr_of_data_words>0)
	{
		if(nr_of_data_words<0x1F){ // nr of data words cannot be 31, since the header is already 2 words
			// normal programming message

			// Calculate checksum.
			for (offset = nr_of_data_words+HEADERLENGTH-1; offset > 0; offset--) {
				calcsum += ((wispData.blockWriteBufPtr[offset] >> 8) & 0xff)+
						(wispData.blockWriteBufPtr[offset] & 0xff);
			}

			// Only do stuff if checksum matches.
			if (calcsum == checksum) {
				checksum = ((address >> 8) & 0xFF) + (address & 0xFF);

				for (offset = 0x00; offset < nr_of_data_words; offset ++) {
					(* (uint16_t *) (address + (offset<<1))) =wispData.blockWriteBufPtr[HEADERLENGTH + offset];
					checksum += (* (uint8_t *) (address + (offset<<1))) +
								(* (uint8_t *) (address + (offset<<1) + 0x01));
				}
				if(!rfid.isEavesDropping){
					if(nr_of_data_words < 8){
						LAST_ACK0_L_CS = (nr_of_data_words<< 8) + checksum;
						LAST_ACK1_ADDR = address;
						// store the ack in FRAM, such that if the wisp dies it can be retrieved and checked (via EPC) easily
					}
					// Send ACK.
					wispData.readBufPtr[result_position++]  = nr_of_data_words;
					wispData.readBufPtr[result_position++]  = checksum;
					wispData.readBufPtr[result_position++]  = (address >> 8)  & 0xFF;
					wispData.readBufPtr[result_position++]  = (address)  & 0xFF;
					wispData.readBufPtr[result_position++]  = 0;
					if(DECOMPRESSION_IS_FINISHED){
						DECOMPRESSION_ENABLE;
					}
				}
			}
		}
		else
		{
			// special programming message = [ 3bit special message code with name "resultpos" | 5bit length=31 | 8bit checksum | 16bit anything with name address ]
//			if(result_position==0){ // 0<<2
////				// set the address that the next read should read
////				calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff);
////
////				if (calcsum == checksum){
////					readBuff16_t[0] = (* (uint16_t *) (address+0));
////					readBuff16_t[1] = (* (uint16_t *) (address+2));
////					readBuff16_t[2] = (* (uint16_t *) (address+4));
////					readBuff16_t[3] = (* (uint16_t *) (address+6));
////					readBuff16_t[4] = (* (uint16_t *) (address+8));
////					readBuff16_t[5] = (* (uint16_t *) (address+10));
////					readBuff16_t[6] = (* (uint16_t *) (address+12));
////					readBuff16_t[7] = (* (uint16_t *) (address+14));
////					readBuff16_t[8] = (* (uint16_t *) (address+16));
////					readBuff16_t[9] = (* (uint16_t *) (address+18));
////					readBuff16_t[10] = (* (uint16_t *) (address+20));
////					readBuff16_t[11] = (* (uint16_t *) (address+22));
////					readBuff16_t[12] = (* (uint16_t *) (address+24));
////					readBuff16_t[13] = (* (uint16_t *) (address+26));
////					readBuff16_t[14] = (* (uint16_t *) (address+28));
////					readBuff16_t[15] = (* (uint16_t *) (address+30));
////				}
//			} else
			if(result_position ==4){ // 1<<2
				calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff);

				if (calcsum == checksum){
					// set the address that the next X reads should read, continuesly
					ADDRESS_TO_READ = address;
					ADDRESS_NR_TO_READ = 0xFF;  // disable this
					my_readCallback();
					LAST_ACK0_L_CS = (nr_of_data_words<< 8) + checksum;
					LAST_ACK1_ADDR = address;
				}
				else
				{
					LAST_ACK0_L_CS = (nr_of_data_words<< 8) + checksum;
					LAST_ACK1_ADDR = address;
				}
			}
			else if(result_position ==8){ //2<<2
				// give a list of 7 start memory locations to read 16 words each, why 7? because you can do max 7 reads in this same accessspec
				calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff) +
						((wispData.blockWriteBufPtr[2] >> 8) & 0xff) + (wispData.blockWriteBufPtr[2] & 0xff) +
						((wispData.blockWriteBufPtr[3] >> 8) & 0xff) + (wispData.blockWriteBufPtr[3] & 0xff) +
						((wispData.blockWriteBufPtr[4] >> 8) & 0xff) + (wispData.blockWriteBufPtr[4] & 0xff) +
						((wispData.blockWriteBufPtr[5] >> 8) & 0xff) + (wispData.blockWriteBufPtr[5] & 0xff) +
						((wispData.blockWriteBufPtr[6] >> 8) & 0xff) + (wispData.blockWriteBufPtr[6] & 0xff) +
						((wispData.blockWriteBufPtr[7] >> 8) & 0xff) + (wispData.blockWriteBufPtr[7] & 0xff);

				if (calcsum == checksum){
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ)) = wispData.blockWriteBufPtr[1];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+2)) = wispData.blockWriteBufPtr[2];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+4)) = wispData.blockWriteBufPtr[3];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+6)) = wispData.blockWriteBufPtr[4];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+8)) = wispData.blockWriteBufPtr[5];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+10)) = wispData.blockWriteBufPtr[6];
					(* (uint16_t *) (LOC_ADDRESS_LIST_TO_READ+12)) = wispData.blockWriteBufPtr[7];
					ADDRESS_NR_TO_READ = 0;
					my_readCallback();
					LAST_ACK0_L_CS = (nr_of_data_words<< 8) + calcsum;
					LAST_ACK1_ADDR = address;

				}
				else
				{
					LAST_ACK0_L_CS = (nr_of_data_words<< 8) + 0xEF;
					LAST_ACK1_ADDR = address;
				}
			} else if (result_position ==12){ // 3<<2
				calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff);

				if (calcsum == checksum){
					for (offset =0;offset<0x80;offset ++){
						(* (uint16_t *) (address + (offset<<1))) = 0xFFFF;
					}
					wispData.readBufPtr[0]  = 0x7F; // 3 <<5|| 0x1F
					wispData.readBufPtr[1]  = calcsum;
					wispData.readBufPtr[2]  = (address >> 8)  & 0xFF;
					wispData.readBufPtr[3]  = address  & 0xFF;
				}
			}
				else	{

				LAST_ACK0_L_CS = (result_position << 8) + 0xEE;
				LAST_ACK1_ADDR = address;
			}
		}

	}
	else
	{   // special programming message = [ 3bit special message code with name "resultpos" | 5bit length=0 | 8bit checksum | 16bit anything with name address ]
		// so resultpos will be abused and holds now the
		// Calculate checksum.
		calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff);


		if (calcsum == checksum){
			if(result_position==0){
				for (offset =0;offset<0x80;offset ++){
					(* (uint16_t *) (address + (offset<<1))) = 0xFFFF;
				}
				wispData.readBufPtr[0]  = 0;
				wispData.readBufPtr[1]  = calcsum;
				wispData.readBufPtr[2]  = (address >> 8)  & 0xFF;
				wispData.readBufPtr[3]  = address  & 0xFF;
			} else if(result_position>0){
				// calculate the crc over a user defined memory space
				wispData.readBufPtr[0]  = (address >> 8)  & 0xFF;
				wispData.readBufPtr[1]  = address  & 0xFF;
				crc = crc16_words(0, (uint16_t*) address   +        0                , 2<<(result_position>>2));
				wispData.readBufPtr[2]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[3]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+ (4<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[4]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[5]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+ (8<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[6]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[7]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+(12<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[8]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[9]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+(16<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[10]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[11]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+ (20<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[12]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[13]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+ (24<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[14]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[15]  = crc  & 0xFF;
				crc = crc16_words(0, (uint16_t*) (address+(28<<(result_position>>2))), 2<<(result_position>>2));
				wispData.readBufPtr[16]  = (crc >> 8)  & 0xFF;
				wispData.readBufPtr[17]  = crc  & 0xFF;
			}
		}
	}

}


/**
 * This implements the user application and should never return
 *
 * Must call WISP_init() in the first line of main()
 * Must call WISP_doRFID() at some point to start interacting with a reader
 */

void main(void) {
	WISP_init();

	BSL_ID = 0x0303;


	if(POWERMEASUREMENTS | DECOMPRESSIONTIMETEST)
		PDIR_AUX1 |= BIT4; //set aux to output

	// Check boot flag, give control of .int 36 .int44 .int45 to app and jump to app.
	if(BSL_STATE == 0xdecd){
		if(DECOMPRESSIONTIMETEST)
			P3OUT |=  BIT4;
		decompression();
		if(DECOMPRESSIONTIMETEST)
			P3OUT &=  ~BIT4;
		BSL_STATE = 0xB105; // if decompression is finished, change BSL_STATE to BIOS
	} else	if (BSL_STATE == 0xB007) {
		if(POWERMEASUREMENTS)
			P3OUT &=  ~BIT4; // set aux off
		else
			if( (* (uint16_t *) (0xFEFE)) != 0xFFFF ) {
				(* (uint16_t *) (0xFDD8)) = (uint16_t) &RX_ISR;
				(* (uint16_t *) (0xFDE8)) = (uint16_t) &Timer0A1_ISR;
				(* (uint16_t *) (0xFDEA)) = (uint16_t) &Timer0A0_ISR;

				(* (uint16_t *) (0xFFD8)) = (* (uint16_t *) (0xFED8));
				(* (uint16_t *) (0xFFE8)) = (* (uint16_t *) (0xFEE8));
				(* (uint16_t *) (0xFFEA)) = (* (uint16_t *) (0xFEEA));

				(*((void (*)(void))(*(unsigned int *)0xFEFE)))();

				return;
			} else{
				BSL_STATE = 0xB105;
			}

	} else if (BSL_STATE == 0xB105) {
		if(POWERMEASUREMENTS)
			P3OUT |=  BIT4; // set aux on
		else
			// this code is redundant: you already are in the bios;)
			//if ((* (uint16_t *) (0xFFD8)) != (uint16_t) &RX_ISR) {
			(* (uint16_t *) (0xFFD8)) = (uint16_t) &RX_ISR;
			//}

			//if ((* (uint16_t *) (0xFFE8)) != (uint16_t) &Timer0A1_ISR) {
			(* (uint16_t *) (0xFFE8)) = (uint16_t) &Timer0A1_ISR;
			//}

			//if ((* (uint16_t *) (0xFFEA)) != (uint16_t) &Timer0A0_ISR) {
			(* (uint16_t *) (0xFFEA)) = (uint16_t) &Timer0A0_ISR;
			//}

	}

	// Register callback functions with WISP comm routines
	WISP_registerCallback_ACK(&my_ackCallback);
	WISP_registerCallback_READ(&my_readCallback);
	WISP_registerCallback_WRITE(&my_writeCallback);
	WISP_registerCallback_BLOCKWRITE(&my_blockWriteCallback);

	if(BSL_STATE == 0xea4e){
		rfid.isEavesDropping = 1;
	} else {
		rfid.isEavesDropping = 0;
	}

	// Initialize BlockWrite buffer.
	uint16_t bwr_array[32] = {0};
	RWData.bwrBufPtr = bwr_array;

	// Get access to EPC, READ, and WRITE data buffers
	WISP_getDataBuffers(&wispData);

	// Set up operating parameters for WISP comm routines
	WISP_setMode( MODE_READ | MODE_WRITE | MODE_USES_SEL);
	//WISP_setAbortConditions(CMD_ID_READ | CMD_ID_WRITE /*| CMD_ID_BLOCKWRITE*/ ); // this abort check is partly disabled in assembly.


	// Set up EPC
	wispData.epcBuf[0] = (BSL_ID >> 8)& 0xFF; 			// WISP ID
	wispData.epcBuf[1] = BSL_ID & 0xFF; 	// WISP ID
	wispData.epcBuf[2] = 0x00;
	wispData.epcBuf[3] = 0x00;
	wispData.epcBuf[4] = 0x00;
	wispData.epcBuf[5] = 0x00;
	wispData.epcBuf[6] = (LAST_ACK0_L_CS >> 8)& 0xFF; // embed the last received message in the epc
	wispData.epcBuf[7] = LAST_ACK0_L_CS & 0xFF;
	wispData.epcBuf[8] = (LAST_ACK1_ADDR >> 8)& 0xFF; // embed the last received message in the epc
	wispData.epcBuf[9] = LAST_ACK1_ADDR & 0xFF;//
	wispData.epcBuf[10]= (BSL_STATE >> 8)& 0xFF; // bios (hi)
	wispData.epcBuf[11]= BSL_STATE & 0xFF; // bios (lo)

	// Talk to the RFID reader.
	while (FOREVER) {
		WISP_doRFID(); // you should never return from of this function
//		BITSET(PLED1OUT,PIN_LED1); // you should never see a led blink
//		BITSET(PLED2OUT,PIN_LED2);
	}
}

