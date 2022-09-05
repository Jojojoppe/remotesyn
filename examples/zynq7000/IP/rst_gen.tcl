create_ip -vlnv xilinx.com:ip:proc_sys_reset -module_name rst_gen
set_property -dict [ list \
    CONFIG.C_EXT_RESET_HIGH {0} \
    CONFIG.C_AUX_RESET_HIGH {0} \
] [ get_ips rst_gen ]