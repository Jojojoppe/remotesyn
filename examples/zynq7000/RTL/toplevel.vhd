library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity toplevel is
    port (
        -- DDR
        DDR_Addr     : inout std_logic_vector(14 downto 0);
        DDR_BankAddr : inout std_logic_vector(2 downto 0);
        DDR_CAS_n    : inout std_logic;
        DDR_Clk_n    : inout std_logic;
        DDR_Clk      : inout std_logic;
        DDR_CKE      : inout std_logic;
        DDR_CS_n     : inout std_logic;
        DDR_DM       : inout std_logic_vector(3 downto 0);
        DDR_DQ       : inout std_logic_vector(31 downto 0);
        DDR_DQS_n    : inout std_logic_vector(3 downto 0);
        DDR_DQS_p    : inout std_logic_vector(3 downto 0);
        DDR_ODT      : inout std_logic;
        DDR_RAS_n    : inout std_logic;
        DDR_DSTRB    : inout std_logic;
        DDR_WEB      : inout std_logic;
        DDR_VRN      : inout std_logic;
        DDR_VRP      : inout std_logic;
        -- FIXED IO
        MIO      : inout std_logic_vector(53 downto 0);
        ps_clk   : inout std_logic;
        ps_porb  : inout std_logic;
        ps_srstb : inout std_logic;
        -- OWN DEFINED
        LED : out std_logic_vector(1 downto 0)
    );
end entity;
architecture structural of toplevel is
    -- ----------
    -- COMPONENTS
    -- ----------
    component zynqps
        port (
            FCLK_CLK0         : out std_logic;
            FCLK_RESET0_N     : out std_logic;
            MIO               : inout std_logic_vector(53 downto 0);
            DDR_CAS_n         : inout std_logic;
            DDR_CKE           : inout std_logic;
            DDR_Clk_n         : inout std_logic;
            DDR_Clk           : inout std_logic;
            DDR_CS_n          : inout std_logic;
            DDR_DRSTB         : inout std_logic;
            DDR_ODT           : inout std_logic;
            DDR_RAS_n         : inout std_logic;
            DDR_WEB           : inout std_logic;
            DDR_BankAddr      : inout std_logic_vector(2 downto 0);
            DDR_Addr          : inout std_logic_vector(14 downto 0);
            DDR_VRN           : inout std_logic;
            DDR_VRP           : inout std_logic;
            DDR_DM            : inout std_logic_vector(3 downto 0);
            DDR_DQ            : inout std_logic_vector(31 downto 0);
            DDR_DQS_n         : inout std_logic_vector(3 downto 0);
            DDR_DQS           : inout std_logic_vector(3 downto 0);
            PS_SRSTB          : inout std_logic;
            PS_CLK            : inout std_logic;
            PS_PORB           : inout std_logic
        );
    end component;
    component rst_gen
        port (
            slowest_sync_clk     : in std_logic;
            ext_reset_in         : in std_logic;
            aux_reset_in         : in std_logic;
            mb_debug_sys_rst     : in std_logic;
            dcm_locked           : in std_logic;
            mb_reset             : out std_logic;
            bus_struct_reset     : out std_logic_vector(0 downto 0);
            peripheral_reset     : out std_logic_vector(0 downto 0);
            interconnect_aresetn : out std_logic_vector(0 downto 0);
            peripheral_aresetn   : out std_logic_vector(0 downto 0)
        );
    end component;
    component heartbeat is
        generic (
            Fin  : integer := 100000000;
            Fout : integer := 8
        );
        port (
            ACLK    : in std_logic;
            ARESETN : in std_logic;
            LED     : out std_logic_vector(1 downto 0)
        );
    end component;
    -- -------
    -- SIGNALS
    -- -------
    signal FCLK_CLK0     : std_logic;
    signal FCLK_RESET0_N : std_logic;
    signal ARESETN : std_logic_vector(0 downto 0);
begin
    heartbeat_i : component heartbeat generic map(
        100000000,
        10
        ) port map(
        ACLK    => FCLK_CLK0,
        ARESETN => ARESETN(0),
        LED     => LED
    );
    zynqps_i : component zynqps port map(
        -- MIO
        MIO => MIO,
        -- CLOCKS
        FCLK_CLK0     => FCLK_CLK0,
        FCLK_RESET0_N => FCLK_RESET0_N,
        -- DDR
        DDR_CAS_n    => DDR_CAS_n,
        DDR_CKE      => DDR_CKE,
        DDR_Clk_n    => DDR_Clk_n,
        DDR_Clk      => DDR_Clk,
        DDR_CS_n     => DDR_CS_n,
        DDR_DRSTB    => DDR_DSTRB,
        DDR_ODT      => DDR_ODT,
        DDR_RAS_n    => DDR_RAS_n,
        DDR_WEB      => DDR_WEB,
        DDR_BankAddr => DDR_BankAddr,
        DDR_Addr     => DDR_Addr,
        DDR_VRN      => DDR_VRN,
        DDR_VRP      => DDR_VRP,
        DDR_DM       => DDR_DM,
        DDR_DQ       => DDR_DQ,
        DDR_DQS_n    => DDR_DQS_n,
        DDR_DQS      => DDR_DQS_p,
        -- PS FIXED IO
        PS_SRSTB => PS_SRSTB,
        PS_CLK   => PS_CLK,
        PS_PORB  => PS_PORB
    );
    rst_gen_i : rst_gen port map(
        slowest_sync_clk => FCLK_CLK0,
        ext_reset_in     => FCLK_RESET0_N,
        aux_reset_in     => '1',
        mb_debug_sys_rst => '0',
        dcm_locked       => '1',
        --mb_reset => mb_reset,
        --bus_struct_reset => bus_struct_reset,
        --peripheral_reset => peripheral_reset,
        --interconnect_aresetn => interconnect_aresetn,
        peripheral_aresetn => ARESETN
    );
end architecture;