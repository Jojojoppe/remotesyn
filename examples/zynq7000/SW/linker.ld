OUTPUT_FORMAT ("elf32-littlearm")

MEMORY
{
  SRAM_0 : ORIGIN = 0x00000000, LENGTH = 0x00030000  /* 192k */
  SRAM_1 : ORIGIN = 0xFFFF0000, LENGTH = 0x00010000  /*  64k */
  DDR_PS : ORIGIN = 0x00100000, LENGTH = 0x0FF00000  /* 256M */
}

EXTERN(__stack_size);
ASSERT(__stack_size, "Must provide a non-zero stack size");

EXTERN(_start);

SECTIONS
{

  .text :
  {
    __stext = .;
    *(.vectortable)          /* Vector table */
    *(.text .text.*)         /* Standard Code */
    *(.rodata .rodata.*)     /* Constants, strings, ... */
    *(.glue_7)               /* Glue ARM to thumb code */
    *(.glue_7t)              /* Glue thumb to ARM code */
    __etext = .;
  } >DDR_PS

  .data :
  {
    . = ALIGN(4);
    __sdata = .;
    *(.data .data.*)
    __edata = .;

  } >DDR_PS

  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    __bss_start__ = .;              /* Used for zeroing bss on startup */
    *(.bss .bss.*)
    __bss_end__ = .;
  } >DDR_PS

  . = ALIGN(4);
  end = .;

  /* Place all stacks in SRAM_1 - need to avoid filling addresses */
  /* 0xfffffe00 to 0xfffffff0 - proc1 is halted running code in this range */
  /* TODO: assert stacks do not step on proc1's code out of reset */
  .stack (NOLOAD) :
  {
    . += __stack_size;
    __proc0_irq_stack = .;
    . += __stack_size;
    __proc0_fiq_stack = .;
    . += __stack_size;
    __proc0_svc_stack = .;
    . += __stack_size;
    __proc0_abt_stack = .;
    . += __stack_size;
    __proc0_und_stack = .;
    . += __stack_size;
    __proc0_sys_stack = .;
    . += __stack_size;
    __proc1_irq_stack = .;
    . += __stack_size;
    __proc1_fiq_stack = .;
    . += __stack_size;
    __proc1_svc_stack = .;
    . += __stack_size;
    __proc1_abt_stack = .;
    . += __stack_size;
    __proc1_und_stack = .;
    . += __stack_size;
    __proc1_sys_stack = .;
    . += __stack_size;
  } >SRAM_1

  .data.ddr :
  {
    *(.data_in_ddr)
  } >DDR_PS

  .note.gnu.build-id : {
    KEEP (*(.note.gnu.build-id))
  } >DDR_PS
}