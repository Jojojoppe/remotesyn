library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
    generic (
        -- Formal generic is used to embed formal validation stuff
        formal          : boolean := false;
        -- Data width
        width           : integer := 16;
        -- Max count
        mxcnt           : integer := 256
    );
    port (
        ACLK            : in std_logic;
        ARESETN         : in std_logic;
        cnt             : out std_logic_vector(width-1 downto 0)
    );
end entity;

architecture behav of counter is
    signal icnt : unsigned (width-1 downto 0);
begin

    cnt <= std_logic_vector(icnt);

    process(ACLK, ARESETN)
    begin
        if ARESETN='0' then
            icnt <= (others=>'0');
        elsif rising_edge(ACLK) then
            if icnt<mxcnt then
                icnt <= icnt + 1;
            else 
                icnt <= (others=>'0');
            end if;
        end if;
    end process;

end architecture;