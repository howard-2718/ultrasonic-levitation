DRIVERS_PER_FPGA = 64

# key: KiCAD net name
# value: SystemVerilog net name


FPGA_PRIMARY_PINOUT = {
    "/PRIMARY_DATA0": "ft_data[0]",
    "/PRIMARY_DATA1": "ft_data[1]",
    "/PRIMARY_DATA2": "ft_data[2]",
    "/PRIMARY_DATA3": "ft_data[3]",
    "/PRIMARY_DATA4": "ft_data[4]",
    "/PRIMARY_DATA5": "ft_data[5]",
    "/PRIMARY_DATA6": "ft_data[6]",
    "/PRIMARY_DATA7": "ft_data[7]",
    "/PRIMARY_TXE": "ft_txen",
    "/PRIMARY_RCXF": "ft_rxfn",
    "/PRIMARY_OEN": "ft_oen",
    "/PRIMARY_SIWU": "ft_siwu",
    "/PRIMARY_WRN": "ft_wrn",
    "/PRIMARY_RDN": "ft_rdn",
    "/FPGA_RESET": "ext_rst",
    **{f"/Connector2/IO_A{i+1}": f"a" for i in range(DRIVERS_PER_FPGA)},
    **{f"/Connector2/IO_B{i+1}": f"a" for i in range(DRIVERS_PER_FPGA)},
    "/SYNC": "sync_out"
}

FPGA_SECONDARY_PINOUT = {
    "/SECONDARY_DATA0": "ft_data[0]",
    "/SECONDARY_DATA1": "ft_data[1]",
    "/SECONDARY_DATA2": "ft_data[2]",
    "/SECONDARY_DATA3": "ft_data[3]",
    "/SECONDARY_DATA4": "ft_data[4]",
    "/SECONDARY_DATA5": "ft_data[5]",
    "/SECONDARY_DATA6": "ft_data[6]",
    "/SECONDARY_DATA7": "ft_data[7]",
    "/SECONDARY_TXE": "ft_txen",
    "/SECONDARY_RCXF": "ft_rxfn",
    "/SECONDARY_OEN": "ft_oen",
    "/SECONDARY_SIWU": "ft_siwu",
    "/SECONDARY_WRN": "ft_wrn",
    "/SECONDARY_RDN": "ft_rdn",
    "/FPGA_RESET": "ext_rst",
    **{f"/FPGA secondary/IO_A_{i+1}": f"a" for i in range(DRIVERS_PER_FPGA)},
    **{f"/FPGA secondary/IO_B_{i+1}": f"a" for i in range(DRIVERS_PER_FPGA)},
    "/SYNC": "sync_in"
}