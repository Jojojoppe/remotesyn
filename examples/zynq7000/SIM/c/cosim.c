#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/select.h>
#include <errno.h>

#include "remote-port-proto.h"
#define UNIX_PREFIX "unix:"

int fd;
uint8_t buf[4096];
struct rp_pkt_hdr * hdr = (struct rp_pkt_hdr*)buf;
struct rp_pkt * payload = (struct rp_pkt*)(buf);
int rp_pkt_id = 0;
struct rp_peer_state state;
size_t pkt_size;
FILE * log;

int still_to_write, still_to_read, datpointer;
uint32_t write_addr, read_addr;

int start_cosim(char * descr){
    // Open socket
    fd = socket(AF_UNIX, SOCK_STREAM, 0);
    // Try to connect
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, descr + strlen(UNIX_PREFIX), sizeof addr.sun_path);
    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) >= 0){
		// log = fopen("cosim_log.txt", "w");
        return 0;
    }else{
        close(fd);
        return 1;
    }
}

void end_cosim(){
    close(fd);
	// fclose(log);
}

int wait_cosim(uint32_t * retaddr, uint32_t * time){
	// fprintf(log, "-->");
    if(still_to_write){
        *retaddr = write_addr;
		// fprintf(log, "\r\nwrite [%08x] @ %d\r\n", *retaddr, *time);
        return 1;
    }else if(still_to_read){
        *retaddr = read_addr;
		// fprintf(log, "\r\nread [%08x] @ %d\r\n", *retaddr, *time);
        return 2;
    }else{
        int n;
        int retval = 0;
        // Receive header
        do{
            n = recv(fd, hdr, sizeof(struct rp_pkt_hdr), 0);
        } while(n<=0);
        rp_decode_hdr(hdr);

		// fprintf(log, " . ");

        // Receive payload
        if(hdr->len){
            do{
                n = recv(fd, hdr+1, hdr->len, 0);
            } while(n<=0);
        }
        rp_decode_payload(payload);

		// fprintf(log, "%d\r\n", hdr->cmd);
        switch(hdr->cmd){

            case RP_CMD_hello:{
                rp_process_caps(&state, buf+payload->hello.caps.offset, payload->hello.caps.len);

                // Send HELO packet
                uint32_t caps[] = {
                    CAP_BUSACCESS_EXT_BASE
                };
                size_t s = rp_encode_hello_caps(rp_pkt_id++, 0, buf, 4, 3, caps, caps, sizeof(caps)/sizeof(uint32_t));
                send(fd, buf, s, 0);
                send(fd, caps, sizeof(caps), 0);
				// fprintf(log, "hello\r\n");
            } break;

			case RP_CMD_interrupt:{
				*time = (uint32_t) payload->interrupt.timestamp;
				// fprintf(log, "interrupt @ %ld\r\n", payload->interrupt.timestamp);
			} break;

            case RP_CMD_write:{
                int addr = payload->busaccess_ext_base.addr;
                int len = payload->busaccess_ext_base.len;
				uint64_t t = payload->busaccess_ext_base.timestamp;

                if(len/4>1){
                    // Must be more than one write cycle
                    still_to_write = len/4-1;
                    write_addr = addr+4;
                    datpointer = 0;
                }else{
                    still_to_write = 0;
                }

                retval = 1;
                *retaddr = addr;
				*time = (uint32_t)t;
				// fprintf(log, "write [%08x] @ %d\r\n", *retaddr, *time);

                // Respond to write
                struct rp_encode_busaccess_in in = {0};
                rp_encode_busaccess_in_rsp_init(&in, payload);
                pkt_size = rp_encode_busaccess(&state, buf, &in);
            } break;

            case RP_CMD_read:{
                int len = payload->busaccess_ext_base.len;
                int addr = payload->busaccess_ext_base.addr;
				uint64_t t = payload->busaccess_ext_base.timestamp;

                if(len/4>1){
                    // Must be more than one write cycle
                    still_to_read = len/4-1;
                    read_addr = addr+4;
                    datpointer = 0;
                }else{
                    still_to_read = 0;
                }

                retval = 2;
                *retaddr = addr;
				*time = (uint32_t)t;
				// fprintf(log, "read [%08x] @ %d\r\n", *retaddr, *time);

                // Respond to read
                struct rp_encode_busaccess_in in = {0};
                rp_encode_busaccess_in_rsp_init(&in, payload);
                pkt_size = rp_encode_busaccess(&state, buf, &in);
            } break;

            case RP_CMD_sync:{
                // Respond to sync
                struct rp_pkt resp = {0};
                size_t s = rp_encode_sync_resp(rp_pkt_id++, 0, &resp, payload->sync.timestamp);
				uint64_t t = payload->sync.timestamp;
				*time = (uint32_t)t;
                send(fd, &resp, s, 0);
				// fprintf(log, "SYNC @ %ld\r\n", payload->sync.timestamp);
            } break;
        }
        return retval;
    }
}

void read_cosim(unsigned int value){
    unsigned int * dat = (unsigned int*)((void*)payload + sizeof(payload->busaccess_ext_base));
    dat[datpointer] = value;
	// fprintf(log, " -> %08x\r\n", value);
}

int write_cosim(){
    unsigned int * dat = (unsigned int*)((void*)payload + sizeof(payload->busaccess_ext_base));
	fprintf(log, " -> %08x\r\n", dat[datpointer]);
    // return dat[datpointer];
}

void finalize_cosim(uint32_t timestamp){
    if(still_to_write){
        still_to_write--;
        write_addr += 4;
        datpointer++;
    }else if(still_to_read){
        still_to_read--;
        read_addr += 4;
        datpointer++;
    }else{
		payload->busaccess_ext_base.timestamp = (uint64_t) timestamp;
        send(fd, buf, pkt_size, 0);
    }
	// fprintf(log, "finalize @ %d\r\n<--\r\n", timestamp);
}