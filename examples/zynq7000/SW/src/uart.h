#ifndef __H_UART
#define __H_UART 1

void uart_send(char c);
char uart_recv();
char uart_recv_blocking();
void uart_setup(void);
void uart_back_up(void);
void uart_puts(char * s);

#endif