import os

# Linux install
os.environ["KICAD8_SYMBOL_DIR"] = "/usr/share/kicad/symbols/"

# Windows install mapped drive
# os.environ["KICAD8_SYMBOL_DIR"] = (
#     "/mnt/c/Program Files/KiCad/8.0/share/kicad/symbols/"
# )


from skidl import *

set_default_tool(KICAD8)

# Nets
net_v5 = Net("+5V")
net_gnd = Net("GND")

net_servo = Net("Servo")
net_analog = Net("Analog")

# Connectors
conn_pwr = Part(
    lib="Connector",
    name="Conn_01x05_Pin",
)

conn_servo = Part(
    lib="Connector",
    name="Screw_Terminal_01x03",
    footprint="TerminalBlock_TE-Connectivity:TerminalBlock_TE_282834-3_1x03_P2.54mm_Horizontal",
)

# Parts
mcu = Part(lib="MCU_Microchip_ATtiny", name="ATtiny85-20P")
pot = Part(lib="Device", name="R_Potentiometer")


# Connections
conn_pwr[1] += net_v5
conn_pwr[1].drive = POWER
conn_pwr[5] += net_gnd
conn_pwr[5].drive = POWER
conn_pwr[2:4] += NC

conn_servo[1] += net_v5
conn_servo[2] += net_servo
conn_servo[2].func = Pin.types.OUTPUT
conn_servo[3] += net_gnd

mcu[:] += NC  # By default, all pins disconnected.
mcu["VCC"] += net_v5
mcu["GND"] += net_gnd
mcu["PB2"] += net_servo
mcu["PB3,p2"] += net_analog

pot[1] += net_v5
pot[2] += net_analog
pot[2].func = Pin.types.INPUT
pot[3] += net_gnd

# Outputs
# generate_netlist(file_="skidl_netlist.net") # Works
# generate_schematic()  # file_="skidl_schematic.sch") # Currently only KiCad 5.1.10
generate_graph()  # DOT
# generate_svg()  # Not working
