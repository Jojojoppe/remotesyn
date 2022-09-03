# Remotesyn

```
$> remotesyn -h
Unified FPGA synthesizer frontend
(c) Joppe Blondel - 2022

Usage: /home/joppe/.local/bin/remotesyn [ OPTIONS ] action [ target ] ...
where OPTIONS := { -h | -l | -s host:port privkey pubkey authorized | -c config | -b build_dir }
      action  := { ip | syn | impl | bit | all | floorplan | sim | init }

Options:
  -h                 Show this help message
  -l                 Local build
  -s <s-info>        Start server with server information s-info. host:port is the address to bind
                     to, privkey and pubkey are the ssh keys of the server and authorized is the
                     authorized_keys file for the SSH server
  -c <file>          Configuration file, defaults to project.cfg
  -b <dir>           Build directory, defaults to .build

Actions:
ip <target>          Generate IP files from vendor provided libraries
syn <target>         Synthesize design for target
impl <target>        Route and place design for target
bit <target>         Generate output files and run analysis for target
all <target>         Generate IP, synthesize, route and place design for target
floorplan <target>   Run floorplan editor, currently only for local execution
sim <simtarget>      Run simulation target
init                 Initialize project
```