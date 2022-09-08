    .syntax unified     /* Use the unified instruction syntax */
    .arm                /* Assemble ARM instruction set, not thumb */

    .equ PROC1_RESET_VECTOR_TABLE,  0xFFFFFFF0

    .equ CPSR_MODE_USER,       0x10
    .equ CPSR_MODE_FIQ,        0x11
    .equ CPSR_MODE_IRQ,        0x12
    .equ CPSR_MODE_SVC,        0x13
    .equ CPSR_MODE_ABORT,      0x17
    .equ CPSR_MODE_UNDEFINED,  0x8B
    .equ CPSR_MODE_SYSTEM,     0x1F

    .equ CPSR_IRQ, 0x80 /* disable IRQ interrupts */
    .equ CPSR_FIQ, 0x40 /* disable FIQ interrupts */

    .global __stack_size
    .equ __stack_size,         0x1000

// ------------------
.section .vectortable
// ------------------
.global vectortable
vectortable:
    /* Exception                Processor Mode          Event                    Return Sequence              */
    b reset_handler             /* MODE_SVC          System Reset                n/a                          */
    b undef_handler             /* MODE_UNDEFINED    Undefined Instruction       MOVS PC, LR (if emulating)   */
    b SVC_handler				/* MODE_SVC          SVC instruction             MOVS PC, LR                  */
    b prefetch_abort_handler    /* MODE_ABORT        Invalid inst. address       SUBS PC, LR, #4              */
    b data_abort_handler        /* MODE_ABORT        R/W to invalid address      SUBS PC, LR, #8 (to retry)   */
    b hypervisor_handler        /* MODE_HYP          Hypervisor entry            ERET                         */
    b IRQ_handler				/* MODE_IRQ          IRQ Input Asserted          SUBS PC, LR, #4              */
    b FIQ_handler               /* MODE_FIQ          FIQ Input Asserted          SUBS PC, LR, #4              */

reset_handler:
	b _start

undef_handler:
    b .

SVC_handler:
    b .

prefetch_abort_handler:
    b .

data_abort_handler:
    b .

hypervisor_handler:
    b . 

IRQ_handler:
    b .

FIQ_handler:
    b .

// -----------
.section .text
// -----------
.global _start
_start:
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_IRQ)       /* switch to MODE_IRQ */
    ldr sp, =__proc0_irq_stack                              /* load IRQ mode stack pointer */
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_FIQ)        /* switch to MODE_FIQ */
    ldr sp, =__proc0_fiq_stack                              /* load FIQ mode stack pointer */
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_ABORT)      /* switch to MODE_ABT */
    ldr sp, =__proc0_abt_stack                              /* load ABT mode stack pointer */
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_UNDEFINED)  /* switch to MODE_UND */
    ldr sp, =__proc0_und_stack                              /* load UND mode stack pointer */
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_SYSTEM)     /* switch to MODE_SYS */
    ldr sp, =__proc0_sys_stack                              /* load SYS mode stack pointer */
    msr CPSR, #(CPSR_IRQ | CPSR_FIQ | CPSR_MODE_SVC)        /* switch to MODE_SVC */
    ldr sp, =__proc0_svc_stack                              /* load SVC mode stack pointer */
    /* We are now in SVC mode */

	/* Set vector table base address */
    ldr r0, =vectortable
    mcr p15, #0, r0, c12, c0, #0

	b main

_hang:
	b _hang

.end