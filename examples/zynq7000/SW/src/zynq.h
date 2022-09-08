#ifndef __H_ZYNQ
#define __H_ZYNQ 1

#define ZYNQ_PERIPH_PHY_BASE		0xF8000000

#define ZYNQ_PERIPH_TTC0_BASE		(ZYNQ_PERIPH_PHY_BASE + 0x1000)

#define ZYNQ_PRI_PERIPH_PHYS_BASE	0xF8F00000
#define ZYNQ_PERIPH_SIZE			0x2000

#define ZYNQ_SCU_PHYS_BASE			(ZYNQ_PRI_PERIPH_PHYS_BASE + 0)
#define ZYNQ_SCU_SIZE				0x0100

#define ZYNQ_GIC_CPU_PHYS_BASE		(ZYNQ_PRI_PERIPH_PHYS_BASE + 0x100)
#define ZYNQ_GIC_CPU_SIZE			0x0100

#define ZYNQ_GTIMER_PHYS_BASE		(ZYNQ_PRI_PERIPH_PHYS_BASE + 0x200)
#define ZYNQ_GTIMER_SIZE			0x0100

#define ZYNQ_PTIMER_WDT_PHYS_BASE	(ZYNQ_PRI_PERIPH_PHYS_BASE + 0x600)
#define ZYNQ_PTIMER_WDT_SIZE		0x0100

#define ZYNQ_GIC_DIST_PHYS_BASE		(ZYNQ_PRI_PERIPH_PHYS_BASE + 0x1000)
#define ZYNQ_GIC_DIST_SIZE			0x1000

#define WRITE32(_reg, _val) (*(volatile uint32_t*)&_reg = _val)
#define WRITE16(_reg, _val) (*(volatile uint16_t*)&_reg = _val)
#define WRITE8(_reg, _val) (*(volatile uint8_t*)&_reg = _val)

#define cpu_disable_interrups() asm ("cpsid if")
#define cpu_enable_interrups() asm ("cpsie if")

#endif