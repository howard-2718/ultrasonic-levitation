import pandas as pd
from net_name_map import FPGA_PRIMARY_PINOUT, FPGA_SECONDARY_PINOUT

PRIMARY = False

OUTPUT_FILE_NAME = "./pin_assignment_scripts/cyclone10_10cl010_u256"


FPGA_CSV_PRI = "./pin_assignment_scripts/fpga_pinout_primary"
FPGA_CSV_SEC = "./pin_assignment_scripts/fpga_pinout_secondary"

CONN_CSV_PRI = "./pin_assignment_scripts/conn_pinout_primary"
CONN_CSV_SEC = "./pin_assignment_scripts/conn_pinout_secondary"

PRIM_CONNS = ["J7", "J6"]
SEC_CONNS = ["J8", "J14"]

def main():
    conn_csv = CONN_CSV_PRI if PRIMARY else CONN_CSV_SEC
    fpga_csv = FPGA_CSV_PRI if PRIMARY else FPGA_CSV_SEC
    name_map = FPGA_PRIMARY_PINOUT if PRIMARY else FPGA_SECONDARY_PINOUT
    conns = PRIM_CONNS if PRIMARY else SEC_CONNS

    df_conn = pd.read_csv(f'{conn_csv}.csv', skiprows=0, usecols=[0, 1, 2])
    df_fpga = pd.read_csv(f'{fpga_csv}.csv', skiprows=0, usecols=[0, 1, 2])

    lines = [
            "#============================================================\n",
            f"# Generated Pin Assignments for {fpga_csv}\n",
            "#============================================================\n\n\n",
    ]

    for net_name in name_map.keys():
        u256_pin = df_fpga.loc[df_fpga["Net"] == net_name]["Pad"].iat[0]
        if name_map[net_name] == "a":

            conn_pad = 64 - int(df_conn.loc[df_conn["Net"] == net_name]["Pad"].iat[0])
            r, c = divmod(conn_pad, 16)
            transducer_index = r*16 + (c if r%2==0 else 16-1-c)

            conn_name = df_conn.loc[df_conn["Net"] == net_name]["Reference"].iat[0]

            if conn_name == conns[1]:
                transducer_index += 64

            sig_name = f"trans[{transducer_index}]"

        else:
            sig_name = name_map[net_name]

        lines.append(f"set_location_assignment PIN_{u256_pin} -to {sig_name}\n")

    num_assignments = len(name_map)

    output_file = OUTPUT_FILE_NAME + ("_primary" if PRIMARY else "_secondary")

    with open(f"{output_file}.qsf", 'w') as output_file:
        output_file.writelines(lines)
    print(f"{num_assignments} pin assignments from {fpga_csv}.csv generated in {OUTPUT_FILE_NAME}.qsf")




if __name__ == "__main__":
    main()