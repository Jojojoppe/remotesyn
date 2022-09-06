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

    f_counter : if formal generate
    begin
        -- Set clock source for all assertions
        default clock is rising_edge(ACLK);
        -- Counter is always under mxcnt if it started under max
        a_never_exceeds_max : assert (always (icnt<mxcnt) -> always (icnt<mxcnt));
        -- Counter is always reset to 0
        a_counter_reset_to_zero : assert (always (ARESETN='0') -> (icnt=0));
    end generate;

    p_counter : process(ACLK, ARESETN)
    begin
        if ARESETN='0' then
            icnt <= (others=>'0');
        elsif rising_edge(ACLK) then
            -- Without this -1 the assertion wont hold
            if icnt<mxcnt-1 then
                icnt <= icnt + 1;
            else 
                icnt <= (others=>'0');
            end if;
        end if;
    end process;

end architecture;