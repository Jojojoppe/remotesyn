#include "ps7_init.h"
#include "zynq.h"
#include "uart.h"
#include "printf.h"

void main(){
    cpu_disable_interrups();
    // Initialize ZYNQ Processing System
    ps7_init();
    // Start UART
    uart_setup();

    printf("Hello World!\n");

}