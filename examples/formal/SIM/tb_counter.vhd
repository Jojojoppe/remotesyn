library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_counter is
end entity;

architecture behav of tb_counter is

    component counter is
        generic (
            formal          : boolean := false;
            width           : integer := 16;
            mxcnt           : integer := 256
        );
        port (
            ACLK            : in std_logic;
            ARESETN         : in std_logic;
            cnt             : out std_logic_vector(width-1 downto 0)
        );
    end component;

    signal ACLK, ARESETN : std_logic := '0';
    signal cnt : std_logic_vector(15 downto 0);

begin

    ACLK <= not ACLK after 10 ns;
    ARESETN <= '1' after 50 ns;

    process
    begin
        wait for 2 us;
        report "END OF SIMULATION" severity failure;
    end process;

    c_counter : component counter
        generic map(
            formal => false,
            width => cnt'length,
            mxcnt => 5
        ) port map (
            ACLK => ACLK,
            ARESETN => ARESETN,
            cnt => cnt
        );
        
end architecture;