#include "ps7_init.h"
#include "zynq.h"
#include "uart.h"
#include "printf.h"

// COSIM control
volatile unsigned int * PAUSE			= (unsigned int*) 0x7ffffff4;		// Pause the cosimulation
volatile unsigned int * SOS				= (unsigned int*) 0x7ffffff8;		// (Re)start the cosimulation
volatile unsigned int * EOS				= (unsigned int*) 0x7ffffffc;		// Stop the cosimulation


void main(){
    cpu_disable_interrups();
    // Initialize ZYNQ Processing System
    // ps7_init();
    // Start UART
    uart_setup();

    *SOS = 1;

    printf("Hello World!\n");

    for(int i=0; i<32; i++){
        printf("i=%d\n", i);
    }

    *EOS = 1;

    for(;;);
}