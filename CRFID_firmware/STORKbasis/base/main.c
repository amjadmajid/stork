
/* Author: Henko Aantjes, and Jethro Tan          
 * Date: 28/07/2016
*/

#include "wisp-base.h"
//#define BSL_VIRTUAL_ID   0x1900
#define BSL_ID           0x1910
#define BSL_PASSWD       0x1920
//(* (uint16_t *) (BSL_PASSWD)) can be boot(b007), bios(b015), eavedropping/sniffing(ea4e) or empty(0)
#define HEADERLENGTH	 2


WISP_dataStructInterface_t wispData;

/**
 * This function is called by WISP FW after a successful ACK reply
 *
 */
void my_ackCallback (void) {
	if(rfid.isEavesDropping){
		wispData.epcBuf[2] = 0x00; // setting 2 and 6 to zero should be enough
		wispData.epcBuf[6] = 0x00;
	}
	asm(" NOP");
}

/**
 * This function is called by WISP FW after a successful read command
 *  reception
 *
 */
void my_readCallback (void) {
	asm(" NOP");
}

/**
 * This function is called by WISP FW after a successful write command
 *  reception
 *
 */
void my_writeCallback (void) {
	// Get data descriptor.
	uint8_t hi = (wispData.writeBufPtr[0] >> 8)  & 0xFF;
	uint8_t lo = (wispData.writeBufPtr[0])  & 0xFF;

	// Write bootloader password if correct command is given.
	if (hi == 0xb1 && lo == 0x05) {
		(* (uint16_t *) (BSL_PASSWD)) = 0xB105; // set password
		rfid.isEavesDropping = 0;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = hi;
		wispData.readBufPtr[1]  = lo;
		wispData.readBufPtr[2]  = 0x00;
		wispData.readBufPtr[3]  = 0x00;
		wispData.readBufPtr[4]  = 0x00;
	} else if (hi == 0xB0 && lo == 0x07) {
		(* (uint16_t *) (BSL_PASSWD)) = 0xB007;
		// POR.
		PMMCTL0 |= PMMSWPOR;
	} else if (hi == 0xea && lo == 0x40){ // command stop eavesdropping
			rfid.isEavesDropping = 0;
			(* (uint16_t *) (BSL_PASSWD)) = 0xB105;
			// Acknowledge the message.
			wispData.readBufPtr[0]  = hi;
			wispData.readBufPtr[1]  = lo;
			wispData.readBufPtr[2]  = 0x00;
			wispData.readBufPtr[3]  = 0x00;
	}
	else if (hi == 0xea && lo == 0x41){ // command stop eavesdropping
		rfid.isEavesDropping = 1;
		(* (uint16_t *) (BSL_PASSWD)) = 0xea4e;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = hi;
		wispData.readBufPtr[1]  = lo;
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
	if(nr_of_data_words>0)
	{   // normal programming message

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
				// Send ACK.
				wispData.readBufPtr[result_position++]  = nr_of_data_words;
				wispData.readBufPtr[result_position++]  = checksum;
				wispData.readBufPtr[result_position++]  = (address >> 8)  & 0xFF;
				wispData.readBufPtr[result_position++]  = (address)  & 0xFF;
				wispData.readBufPtr[result_position++]  = 0;
			} else{
				// send ack in EPC
				if((wispData.epcBuf[2]>0) && (wispData.epcBuf[6] == 0)){
					wispData.epcBuf[6]  = nr_of_data_words;
					wispData.epcBuf[7]  = checksum;
					wispData.epcBuf[8]  = (address >> 8)  & 0xFF;
					wispData.epcBuf[9]  = (address)  & 0xFF;
				} else {
					wispData.epcBuf[2]  = nr_of_data_words;
					wispData.epcBuf[3]  = checksum;
					wispData.epcBuf[4]  = (address >> 8)  & 0xFF;
					wispData.epcBuf[5]  = (address)  & 0xFF;
				}
			}
		} 

	}
	else
	{   // special programming message

		// Calculate checksum.
		calcsum = ((wispData.blockWriteBufPtr[1] >> 8) & 0xff) + (wispData.blockWriteBufPtr[1] & 0xff);


		if (calcsum == checksum){
			if(address == 0x10c0) { // loc(k) = False, unlock booting
				checksum = ( ((address >> 8) & 0xFF) + (address & 0xFF)+0xab+0x1e) & 0xFF;
			}
			// Send ACK.
			wispData.readBufPtr[0]  = nr_of_data_words;
			wispData.readBufPtr[1]  = checksum;
			wispData.readBufPtr[2]  = 0xab;
			wispData.readBufPtr[3]  = 0x1e;
			wispData.readBufPtr[4]  = 0x00;
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

	// Check boot flag, give control of .int 36 .int44 .int45 to app and jump to app. (manually change interrupt vectors)
	if ((* (uint16_t *) (BSL_PASSWD)) == 0xB007) {
		(* (uint16_t *) (0xFDD8)) = (uint16_t) &RX_ISR;
		(* (uint16_t *) (0xFDE8)) = (uint16_t) &Timer0A1_ISR;
		(* (uint16_t *) (0xFDEA)) = (uint16_t) &Timer0A0_ISR;

		(* (uint16_t *) (0xFFD8)) = (* (uint16_t *) (0xFED8));
		(* (uint16_t *) (0xFFE8)) = (* (uint16_t *) (0xFEE8));
		(* (uint16_t *) (0xFFEA)) = (* (uint16_t *) (0xFEEA));

		(*((void (*)(void))(*(unsigned int *)0xFEFE)))();

		return;

	} else if ((* (uint16_t *) (BSL_PASSWD)) == 0xB105) {
		(* (uint16_t *) (0xFFD8)) = (uint16_t) &RX_ISR;
		(* (uint16_t *) (0xFFE8)) = (uint16_t) &Timer0A1_ISR;
		(* (uint16_t *) (0xFFEA)) = (uint16_t) &Timer0A0_ISR;
	}

	// Register callback functions with WISP comm routines
	WISP_registerCallback_ACK(&my_ackCallback);
	WISP_registerCallback_READ(&my_readCallback);
	WISP_registerCallback_WRITE(&my_writeCallback);
	WISP_registerCallback_BLOCKWRITE(&my_blockWriteCallback);

	if((* (uint16_t *) (BSL_PASSWD)) == 0xea4e){
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

	(* (uint16_t *) (BSL_ID)) = 0x0301;
	// Set up EPC
	wispData.epcBuf[0] = ((* (uint16_t *) (BSL_ID))>> 8)& 0xFF; 			// WISP ID
	wispData.epcBuf[1] = (* (uint16_t *) (BSL_ID))  & 0xFF; 	// WISP ID
	wispData.epcBuf[2] = 0x00;
	wispData.epcBuf[3] = 0x00;
	wispData.epcBuf[4] = 0x00;
	wispData.epcBuf[5] = 0x00;
	wispData.epcBuf[6] = 0x00;
	wispData.epcBuf[7] = 0x00;
	wispData.epcBuf[8] = 0x00;
	wispData.epcBuf[9] = 0x00; //
	wispData.epcBuf[10]= 0xb1; // bios (hi)
	wispData.epcBuf[11]= 0x05; // bios (lo)

	// Talk to the RFID reader.
	while (FOREVER) {
		WISP_doRFID(); // you should never return from of this function
		BITSET(PLED1OUT,PIN_LED1); // you should never see a led blink
		BITSET(PLED2OUT,PIN_LED2);
	}
}

