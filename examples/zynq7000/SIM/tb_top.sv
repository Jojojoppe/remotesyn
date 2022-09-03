`timescale 1ns / 1ps

module tb_top ();

	reg ACLK   ;
	reg ARESETN;

	initial begin
		ACLK = 1'b0;
	end

	always #5 ACLK = !ACLK;

	initial begin
		ARESETN = 1'b0;
		tb_top.ps.inst.fpga_soft_reset(32'h1);
		repeat(20)@(posedge ACLK);
		ARESETN = 1'b1;
		tb_top.ps.inst.fpga_soft_reset(32'h0);
		repeat(5)@(posedge ACLK);

		repeat(100)@(posedge ACLK);
		// Write some data
		//tb_top.ps.inst.write_data(32'h40000000, 4, 32'hdeadbeef, resp);
		//tb_top.ps.inst.write_data(32'h40000004, 16, 128'habcdef0185274123deadbeef95123578, resp);

		$display("End of simulation");
		$stop;
	end

	zynq_ps ps (
		.PS_CLK           (ACLK         ),
		.PS_SRSTB         (ARESETN      ),
		.PS_PORB          (ARESETN      )
	);
endmodule