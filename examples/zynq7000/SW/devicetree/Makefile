.SILENT:

TARGET				:= system.dtb

BUILDROOT			?= $(shell pwd)
BUILDDIR			:= build

.PHONY: $(TARGET) all clean
all: $(TARGET)

$(TARGET):
	gcc -I $(BUILDROOT) -I $(BUILDROOT)/include -E -nostdinc -undef -D__DTS__ -x assembler-with-cpp -o system.dts $(BUILDROOT)/system-top.dts
	dtc -I dts -O dtb -o system.dtb system.dts