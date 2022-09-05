library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

entity tb_heartbeat is
end entity;

architecture behavioural of tb_heartbeat is
    -- COMPONENTS
    -- ----------
    component heartbeat is
        -- generic (
            -- Fin  : integer := 100000000;
            -- Fout : integer := 8
        -- );
        port (
            ACLK    : in std_logic;
            ARESETN : in std_logic;
            LED     : out std_logic_vector(1 downto 0)
        );
    end component;
    -- SIGNALS
    -- -------
    signal ACLK : std_logic := '0';
    signal LED : std_logic_vector(1 downto 0) := "00";
    signal ARESETN : std_logic := '0';
begin
    c_heartbeat : component heartbeat 
    -- generic map(
    --     50000000,
    --     5000000
    -- ) 
    port map(
        ACLK    => ACLK,
        ARESETN => ARESETN,
        LED     => LED
    );
    ACLK <= not ACLK after 10 ns;
    ARESETN <= '1' after 150 ns;

    process
    begin
        wait for 5000 ns;
        report "END OF SIMULATION" severity failure;
    end process;
end architecture;