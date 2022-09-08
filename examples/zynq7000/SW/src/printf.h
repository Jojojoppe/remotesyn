#ifndef __H_KPRINTF
#define __H_KPRINTF 1

#include <stdarg.h>

int printf(char * fmt, ...);
int sprintf(char * buf, char * fmt, ...);

void hexDump (const char * desc, const void * addr, const int len);

#endif