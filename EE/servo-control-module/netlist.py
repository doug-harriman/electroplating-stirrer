# Idea:
# If we define connector pins as "input" or "output", we can
# trace back to the MCU pin and determine if it is an input or output.
# Then we can generate commments to help with pin configuration.

from kinparse import parse_netlist

# TODO: Define some macros that define pin based on connection.

# Read the netlist
fn = "servo-control-module.net"
nl = parse_netlist(fn).as_dict()

# Generate dict of components keyed by ref
parts = {p["ref"]: p for p in nl["parts"]}

# Generate dict of nets keyed by net name.
nets = {p["name"]: p for p in nl["nets"]}

# TODO: Drop nets not connected to an MCU.

# Drop unconnected nets
nets = {k: v for k, v in nets.items() if not k.startswith("unconnected-")}

# Drop the power nets
nets.pop("+5V")
nets.pop("GND")

# MCU data sheets.
for ref, data in parts.items():
    if ref.startswith("U"):
        if "datasheet" in data:
            print(f"  // MCU: {data['value']} ({ref})")
            print(f'  // Datasheet: {data["datasheet"]}')
print("")


# Active part pin mappings.
for net, nodes in nets.items():
    nodes = nodes["pins"]
    if len(nodes) != 2:
        print(f"Net '{net}' not a simple net, skipping\n")
        continue

    if nodes[0]["ref"].startswith("U"):
        mcu = nodes[0]
        device = nodes[1]
    elif nodes[1]["ref"].startswith("U"):
        mcu = nodes[1]
        device = nodes[0]
    else:
        print(f"Net '{net}' does not have a MCU pin, skipping.\n")
        continue

    # Look for LED's
    # Pin 2 acts as input
    if parts[device["ref"]] == "LED":
        if device["pin"] == "2":
            device["type"] = "input"

    if device["type"] == "input":
        mcu_dir = "output"
        mcu_dir_arrow = "->"
    elif device["type"] == "output":
        mcu_dir = "input"
        mcu_dir_arrow = "<-"
    else:
        mcu_dir = "unknown"
        mcu_dir_arrow = "<-??->"

    mcu_name = parts[mcu["ref"]]["value"]
    device_name = parts[device["ref"]]["value"]
    print(
        f"  // Net {net}: {mcu_name} ({mcu['ref']}) pin {mcu['num']} {mcu_dir_arrow} {device_name} ({device['ref']}) pin {device['num']}"
    )
    # MCU Port extraction
    # TODO: This should be smarter in looking for PxYY name.
    fcn = mcu["function"].split("/")[-1]
    port = fcn[1]
    print(f"  // {fcn} as {mcu_dir} ")

    # Clean up device name.
    device_name = device_name.replace(" ", "_")

    # Macro
    pin_name = f"PIN_{device_name}"
    print(f"  #define {pin_name} ({fcn})")

    # FW Note
    if mcu_dir == "output":
        print(f"  DDR{port} |= (1 << {pin_name});")
    elif mcu_dir == "input":
        print(f"  DDR{port} &= ~(1 << {pin_name});")

    print("")
