library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

entity tb_toplevel is
end entity;

architecture behavioural of tb_toplevel is

    -- COMPONENTS
    -- ----------
    component toplevel is
        port (
            ACLK    : in std_logic;
            LED : out std_logic_vector(7 downto 0);
            SW : in std_logic_vector(3 downto 0)
        );
    end component;

    -- SIGNALS
    -- -------
    signal ACLK : std_logic := '0';
    signal LED : std_logic_vector(7 downto 0) := "00000000";
    signal SW : std_logic_vector(3 downto 0) := "0111";

begin

    c_toplevel : component toplevel port map(
        ACLK, LED, SW
    );

    ACLK <= not ACLK after 10 ns;
    SW(3) <= '1' after 150 ns;

    process
    begin
        wait until SW(3)='1';

        SW(2 downto 0) <= "101";
        wait for 75 ns;
        SW(2 downto 0) <= "010";
        wait for 19 ns;
        SW(2 downto 0) <= "111";

        wait for 100 ns;
        report "END OF SIMULATION" severity failure;
    end process;

end architecture;