`timescale 1ns / 1ps

module tb_cosim;
    import "DPI-C" function int start_cosim(string path);
    import "DPI-C" function void end_cosim();
    import "DPI-C" function int wait_cosim(output int addr, output int t);
    import "DPI-C" function void finalize_cosim(int t);
    import "DPI-C" function void read_cosim(input int value);
    import "DPI-C" function int write_cosim();
    
	// Cosimulation variables
    integer cosim_ret;
    reg unsigned [31:0] cosim_address;
    reg unsigned [31:0] cosim_data;
	integer timestamp;
	integer curtime;
	integer started;

    reg ACLK;
    reg ARESETN;

    wire [1:0] LED;

    initial begin
        ACLK = 1'b0;
        ARESETN = 0'b0;
    end

    always #5 ACLK = !ACLK;

    initial begin
        $display("Starting testbench");
        // Start co-simulation
        if (start_cosim("unix:/tmp/qemu-rport-_cosim@0")>0) begin
            $display("ERROR: Could not start co-simulation. Stop simulation");
            $stop;
        end
        $display("Co-simulation started");
        
        ARESETN = 1'b0;
        repeat(2)@(posedge ACLK);
        ARESETN = 1'b1;
        repeat(2)@(posedge ACLK);

        // Main loop
        cosim_ret = 0;
        while (cosim_ret>=0) begin
            cosim_ret = wait_cosim(cosim_address, timestamp);

            // Check for end of simulation
            if (cosim_address=='h7ffffffc) begin
                break;
            end

			// Check for start of simulation
			if (cosim_address=='h7ffffff8) begin
				curtime = timestamp;
				cosim_ret = 0;
				started = 1;
			end

			// Check for pause of simulation
			if (cosim_address=='h7ffffff4) begin
				started = 0;
				finalize_cosim(curtime);
			end

			if (started==0) begin
				continue;
			end

			while(curtime<timestamp) begin
				@(posedge ACLK);
			end

            if (cosim_ret==1) begin
                // WRITE
                cosim_data = write_cosim();
				// ADDR = cosim_address;
				// WRDAT = cosim_data;
				// WR = 1'b1;
				@(posedge ACLK);
				// WR = 1'b0;
				// while (WRREADY==1'b0) begin
				// 	@(posedge ACLK);
				// end
            end

            if (cosim_ret==2) begin
                // READ
				// ADDR = cosim_address;
				// RD = 1'b1;
				@(posedge ACLK);
				// RD = 1'b0;
				// while (RDREADY==1'b0) begin
				// 	@(posedge ACLK);
				// end
				@(negedge ACLK);
				cosim_data = 'hdeadbeef;
                read_cosim(cosim_data);
            end
            finalize_cosim(curtime);
        end

        $display("Reached end of simulation. Stop Co-simulation");
        end_cosim();
        $stop;

    end

    heartbeat #(100000000, 10000000) i_heartbeat(
        ACLK, ARESETN, LED
    );

endmodule