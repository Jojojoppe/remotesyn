library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

entity toplevel is
    port (
        ACLK : in std_logic;
        LED  : out std_logic_vector(7 downto 0);
        SW   : in std_logic_vector(3 downto 0)
    );
end toplevel;

architecture structural of toplevel is
    signal ARESETN : std_logic;
begin

    ARESETN <= SW(3);

    process(ACLK, ARESETN)
    begin
        if ARESETN='0' then
            LED <= "11111111";
        elsif rising_edge(ACLK) then
            LED <= SW & SW;
        end if;
    end process;

end architecture;