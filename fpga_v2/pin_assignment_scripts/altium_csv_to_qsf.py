import pandas as pd
from net_name_map import FPGA_PRIMARY_PINOUT, FPGA_SECONDARY_PINOUT

# Parameters
CSV_NAME = "./pin_assignment_scripts/fpga_pinout_secondary"
OUTPUT_FILE_NAME = "./pin_assignment_scripts/cyclone10_10cl010_u256_secondary"
NET_NAME_MAP = FPGA_SECONDARY_PINOUT

def main():
    df = pd.read_csv(f'{CSV_NAME}.csv', skiprows=0, usecols=[0, 1, 2])

    lines = [
            "#============================================================\n",
            f"# Generated Pin Assignments for {CSV_NAME}\n",
            "#============================================================\n\n\n",
    ]

    for net_name in NET_NAME_MAP.keys():
        print(net_name)
        u256_pin = df.loc[df["Net"] == net_name]["Pad"].iat[0]
        lines.append(f"set_location_assignment PIN_{u256_pin} -to {NET_NAME_MAP[net_name]}\n")

    num_assignments = len(NET_NAME_MAP)
    with open(f"{OUTPUT_FILE_NAME}.qsf", 'w') as output_file:
        output_file.writelines(lines)
    print(f"{num_assignments} pin assignments from {CSV_NAME}.csv generated in {OUTPUT_FILE_NAME}.qsf")

if __name__ == "__main__":
    main()