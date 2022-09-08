.SILENT:

TARGET				:= app.elf

BUILDDIR			:= build

SRCDIRS				:= src
SRCFILESC			:= $(shell find $(SRCDIRS) -type f -name "*.c") 
OBJFILESC			:= $(SRCFILESC:%.c=$(BUILDDIR)/%.c.o) $(BUILDDIR)/src/ps7_init.o
DEPFILESC			:= $(SRCFILESC:%.c=$(BUILDDIR)/%.c.d)
SRCFILESA			:= $(shell find $(SRCDIRS) -type f -name "*.S")
OBJFILESA			:= $(SRCFILESA:%.S=$(BUILDDIR)/%.S.o)
DEPFILESA			:= $(SRCFILESA:%.S=$(BUILDDIR)/%.S.d)
SRCFILES			:= $(SRCFILESC) $(SRCFILESA)
OBJFILES			:= $(OBJFILESA) $(OBJFILESC)
DEPFILES			:= $(DEPFILESC) $(DEPFILESA)

FILESTOCLEAN		:= $(OBJFILES) $(DEPFILES) $(BUILDDIR)/$(TARGET)

CROSS_COMPILE		?= arm-none-eabi-
CC					:= $(CROSS_COMPILE)gcc
AS					:= $(CROSS_COMPILE)as
LD					:= $(CROSS_COMPILE)gcc

CC_WARNING			:= -Wall -Wextra
CC_LIBS				:= -lgcc
CC_FLAGS			:= -nostdlib -fno-builtin -g -mcpu=cortex-a9
CC_INCLUDES			:= -I src -I ../OUT/ip/zynqps
LD_FLAGS			:= -Wl,-Tlinker.ld

.PHONY: $(TARGET) all clean
all: $(TARGET)

# PHONY RULES
# -----------

$(TARGET): $(BUILDDIR)/$(TARGET)

clean:
	echo CLEAN FILES FOR $(TARGET)
	-rm -r $(FILESTOCLEAN)

# SPECIFIC BUILD RULES
# --------------------

$(BUILDDIR)/$(TARGET): $(OBJFILES)
	echo 'LD ' $@
	$(LD) $(CC_FLAGS) $(LD_FLAGS) -o $(BUILDDIR)/$(TARGET) $(OBJFILES) $(CC_LIBS)
	$(XILINX_BASE)/bin/$(CROSS_COMPILE)objdump -D $(BUILDDIR)/$(TARGET) > DISASS

$(BUILDDIR)/src/ps7_init.o : ../OUT/ip/zynqps/ps7_init.c ../OUT/ip/zynqps/ps7_init.h
	echo 'CC ' $@
	-mkdir -p $(shell dirname $@)
	$(CC) $(CC_FLAGS) $(CC_WARNING) $(CC_INCLUDES) -MD -o $(BUILDDIR)/src/ps7_init.o -c ../OUT/ip/zynqps/ps7_init.c

$(OBJFILES): $(BUILDDIR)/%.c.o: %.c
	echo 'CC ' $@
	-mkdir -p $(shell dirname $@)
	$(CC) $(CC_FLAGS) $(CC_WARNING) $(CC_INCLUDES) -MD -o $@ -c $<

$(OBJFILESA): $(BUILDDIR)/%.S.o: %.S
	echo 'AS ' $@
	-mkdir -p $(shell dirname $@)
	$(CC) $(CC_FLAGS) $(CC_WARNING) $(CC_INCLUDES) -MD -o $@ -c $<

# Add DEPFILE dependencies
-include $(DEPFILES)