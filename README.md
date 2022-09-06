# Remote synthesis abstraction tool
Remotesyn is a tool which proves a general abstraction for HDL/FPGA toolchains such as Vivado or ISE Webpack. The provided abstractions are: 
+ GHDL simulation [`ghdl`] 
+ SymbiYosys formal verification [`symbiyosys`] 
+ Xilinx ISE synthesis and bitstream generation [`ISE`] 
+ Xilinx ISE IP core generation [`ISE-IP`] 
+ Xilinx isim (ISE) simulation (pre and post synthesis) [`isim`]
+ Xilinx VIVADO synthesis and bitstream generation [`VIVADO`] 
+ Xilinx Vivado IP core generation [`VIVADO-IP`] 
+ Xilinx xsim (Vivado) simulation (pre and post synthesis) [`xsim`] 

The HDL project is configured with a config file (in ini format) and should provide execution targets specified by a `[target.<target_name>]` tag with a toolchain setting (see the example directory for examples). 

This package provides 3 executables: 
+ `rbuild` for local execution of the toolchains, see `rbuild -h` for more information 
+ `rmbuild` for remote execution of the toolchains, see `rmbuild -h` for more information. The project configuration file should contain a server section with SSH settings 
+ `rmserver` for the server side which will execute `rbuild` when asked by `rmbuild`. Execution should be done with `rmserver host port privkeyfile pubkeyfile authorized_hosts_file`

Installing can be done with `pip3`. Currently the package is not yet in the online repositories so a local installation should be done.