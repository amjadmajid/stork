
/** @file		main.c
 * 	@brief		bootloadable minimalistic example
 *
 * 	@author		--
 */

#include "wisp-base.h"
#define BSL_PASSWD       0x1920
#define BSL_ID           0x1910
WISP_dataStructInterface_t wispData;

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
	if (hi == 0xB1 && lo == 0x05) {
		(* (uint16_t *) (BSL_PASSWD)) = 0xB105;

		(* (uint16_t *) (0xFFD8)) = (* (uint16_t *) (0xFDD8));
		(* (uint16_t *) (0xFFE8)) = (* (uint16_t *) (0xFDE8));
		(* (uint16_t *) (0xFFEA)) = (* (uint16_t *) (0xFDEA));

		// POR.
		PMMCTL0 |= PMMSWPOR;
	} else if (hi == 0xB0 && lo == 0x07) {
		// you already are in the BOOT
		(* (uint16_t *) (BSL_PASSWD)) = 0xB007;
		// Acknowledge the message.
		wispData.readBufPtr[0]  = hi;
		wispData.readBufPtr[1]  = lo;
		wispData.readBufPtr[2]  = 0x00;
		wispData.readBufPtr[3]  = 0x00;
		wispData.readBufPtr[4]  = 0x00;
	}

}

/**
 * Generates and stores a table of random numbers into Info Mem segment B/C.
 *  These are used by the WISP as a unique ID and for RN16 generation in Aloha protocol.
 */
void main (void) {

	WISP_init();
	BITCLR(PLED2OUT,PIN_LED1);
	if ((* (uint16_t *) (BSL_PASSWD)) == 0xB007) {
		// this code is redundant: you already are in the boot;)
		(* (uint16_t *) (0xFFD8)) = (uint16_t) &RX_ISR;

		(* (uint16_t *) (0xFFE8)) = (uint16_t) &Timer0A1_ISR;

		(* (uint16_t *) (0xFFEA)) = (uint16_t) &Timer0A0_ISR;
	}

	// Register callback functions with WISP comm routines
	WISP_registerCallback_WRITE(&my_writeCallback);

	// Get access to EPC, READ, and WRITE data buffers
  	WISP_getDataBuffers(&wispData);


  	// Set up operating parameters for WISP comm routines
	WISP_setMode( MODE_READ | MODE_WRITE | MODE_USES_SEL);
	//WISP_setAbortConditions(CMD_ID_READ | CMD_ID_WRITE /*| CMD_ID_BLOCKWRITE*/ ); // this abort check is disabled in assembly.

	// Set up EPC
	wispData.epcBuf[0] = ((* (uint16_t *) (BSL_ID))>> 8)& 0xFF; 			// WISP ID
	wispData.epcBuf[1] = (* (uint16_t *) (BSL_ID))  & 0xFF; 	// WISP ID
	wispData.epcBuf[2] = 0x00; // Header
	wispData.epcBuf[3] = 0x1e; // Header
	wispData.epcBuf[4] = 0xd1; // Address
	wispData.epcBuf[5] = 0x0f; // Address
	wispData.epcBuf[6] = 0xf0; // Checksum
	wispData.epcBuf[7] = 0xff;
	wispData.epcBuf[8] = 0x11;
	wispData.epcBuf[9] = 0x11; // RFID Status/Control
	wispData.epcBuf[10]= 0x11; // RFID Status/Control
	wispData.epcBuf[11]= 0x11;

	//BITSET(PLED2OUT,PIN_LED1);

	while(FOREVER) {
		WISP_doRFID();
	}

}


