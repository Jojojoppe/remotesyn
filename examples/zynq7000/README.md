# ZYNQ 7000 example

Create IP files: `remotesyn -l ip total`<br>
Run full toolchain: `remotesyn -l all total`<br>
Run simulation (first one should create IP files for the sim targets): `remotesyn -l sim presim_total`<br>
Run post-simulation (after synthesis and implementation): `remotesyn -l sim postsim_total`<br>
