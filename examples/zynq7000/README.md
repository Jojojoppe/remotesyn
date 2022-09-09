# ZYNQ 7 series project

### Basic FPGA workflow
+ target `ip`: Generate IP blocks defined in the tcl files in the IP directory
+ target `synth`: Synthesize design
+ target `sim`: Behavioural simulation of part of the design
+ target `psim`: Post synthesis simulation of mentioned part of the design

### ZYNQ SoC workflos
+ target `firmware`: Compile the firmware running on the ARM core(s) with the `make` toolchain
+ target `firmsim`: Simulate the firmware with QEMU without PS/PL cosimulation with the `qemu` toolchain
+ target `devtree`: Compile the device tree for a PS/PL cosimulation with QEMU
+ target `cosim_ps`: PS part of the cosimulation. Must be ran first
+ target `cosim_pl`: PL part of the cosimulation. Must be ran in a separate terminal while the PS part is still running

### Notes:
Compilation with Xilinx provided gcc and binutils done with `xsc` can be problematic... This is the reason
Questasim is used for the cosimulation. If one would use the free Intel variant of Questasim post synthesis
simulation will not be possible. The attempt to get DPI-C working with xsim is not stopped!