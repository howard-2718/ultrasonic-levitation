import pcbnew
import csv

FPGA_REFERENCE = "U10"     #U12 - Primary, U10 - Secondary
OUTPUT_FILE = "fpga_pinout_secondary.csv"

board = pcbnew.GetBoard()

rows = []

for footprint in board.GetFootprints():

    if footprint.GetReference() == FPGA_REFERENCE:

        for pad in footprint.Pads():

            netname = pad.GetNetname()

            # Skip pads that are not connected to any net
            if netname == "" or netname == "":

                continue

            rows.append([
                footprint.GetReference(),
                pad.GetName(),
                netname
            ])

# Sort pins by pad name (nice for FPGA pinouts)
rows.sort(key=lambda x: x[1])

with open(OUTPUT_FILE, "w", newline="") as f:

    writer = csv.writer(f)
    writer.writerow(["Reference", "Pad", "Net"])
    writer.writerows(rows)

print(f"Exported {len(rows)} connected FPGA pins to {OUTPUT_FILE}")