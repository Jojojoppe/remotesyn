library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity heartbeat is
    generic (
        Fin  : integer := 100000000;
        Fout : integer := 8
    );
    port (
        ACLK    : in std_logic;
        ARESETN : in std_logic;
        LED     : out std_logic_vector(1 downto 0)
    );
end entity;

architecture structural of heartbeat is
    signal iLED : std_logic_vector(1 downto 0);
begin

    LED <= iLED;

    process (ACLK, ARESETN)
        variable cnt : integer range 0 to Fin/(2 * Fout) - 1 := 0;
    begin
        if ARESETN = '0' then
            cnt := 0;
            iLED <= "01";
        elsif rising_edge(ACLK) then
            if (cnt = Fin/(2 * Fout) - 1) then
                cnt := 0;
                iLED <= not iLED;
            else
                cnt := cnt + 1;
            end if;
        end if;
    end process;

end architecture;