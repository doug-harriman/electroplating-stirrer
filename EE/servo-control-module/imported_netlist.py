# -*- coding: utf-8 -*-

from skidl import *


def L___home__harriman__Projects__Elecroplating_Stirrer__EE__servo_control_module__servo_control_module_kicad_sch():

    #===============================================================================
    # Component templates.
    #===============================================================================

    Connector_Conn_01x05_Pin_Library_USB_micro_breakout = Part('Connector', 'Conn_01x05_Pin', dest=TEMPLATE, footprint='Library:USB-micro-breakout')
    setattr(Connector_Conn_01x05_Pin_Library_USB_micro_breakout, 'Footprint', 'Library:USB-micro-breakout')
    setattr(Connector_Conn_01x05_Pin_Library_USB_micro_breakout, 'Datasheet', '')
    setattr(Connector_Conn_01x05_Pin_Library_USB_micro_breakout, 'Description', '')

    Connector_Screw_Terminal_01x03_TerminalBlock_TE_Connectivity_TerminalBlock_TE_282834_3_1x03_P2_54mm_Horizontal = Part('Connector', 'Screw_Terminal_01x03', dest=TEMPLATE, footprint='TerminalBlock_TE-Connectivity:TerminalBlock_TE_282834-3_1x03_P2.54mm_Horizontal')
    setattr(Connector_Screw_Terminal_01x03_TerminalBlock_TE_Connectivity_TerminalBlock_TE_282834_3_1x03_P2_54mm_Horizontal, 'Footprint', 'TerminalBlock_TE-Connectivity:TerminalBlock_TE_282834-3_1x03_P2.54mm_Horizontal')
    setattr(Connector_Screw_Terminal_01x03_TerminalBlock_TE_Connectivity_TerminalBlock_TE_282834_3_1x03_P2_54mm_Horizontal, 'Datasheet', '')
    setattr(Connector_Screw_Terminal_01x03_TerminalBlock_TE_Connectivity_TerminalBlock_TE_282834_3_1x03_P2_54mm_Horizontal, 'Description', '')

    Device_R_Potentiometer_Library_Potentiometer_Amazon_Single_Horizontal = Part('Device', 'R_Potentiometer', dest=TEMPLATE, footprint='Library:Potentiometer_Amazon_Single_Horizontal')
    setattr(Device_R_Potentiometer_Library_Potentiometer_Amazon_Single_Horizontal, 'Footprint', 'Library:Potentiometer_Amazon_Single_Horizontal')
    setattr(Device_R_Potentiometer_Library_Potentiometer_Amazon_Single_Horizontal, 'Datasheet', '')
    setattr(Device_R_Potentiometer_Library_Potentiometer_Amazon_Single_Horizontal, 'Description', '')

    MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm = Part('MCU_Microchip_ATtiny', 'ATtiny85-20P', dest=TEMPLATE, footprint='Package_DIP:DIP-8_W7.62mm')
    setattr(MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm, 'Inventree', 'http://192.168.0.120:8800/part/4/')
    setattr(MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm, 'Footprint', 'Package_DIP:DIP-8_W7.62mm')
    setattr(MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm, 'Datasheet', 'http://ww1.microchip.com/downloads/en/DeviceDoc/atmel-2586-avr-8-bit-microcontroller-attiny25-attiny45-attiny85_datasheet.pdf')
    setattr(MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm, 'Description', '')


    #===============================================================================
    # Component instantiations.
    #===============================================================================

    J1 = Connector_Conn_01x05_Pin_Library_USB_micro_breakout(ref='J1', value='USB')

    J2 = Connector_Screw_Terminal_01x03_TerminalBlock_TE_Connectivity_TerminalBlock_TE_282834_3_1x03_P2_54mm_Horizontal(ref='J2', value='SERVO')

    RV1 = Device_R_Potentiometer_Library_Potentiometer_Amazon_Single_Horizontal(ref='RV1', value='POT 100k')

    U1 = MCU_Microchip_ATtiny_ATtiny85_20P_Package_DIP_DIP_8_W7_62mm(ref='U1', value='ATtiny85-20P')


    #===============================================================================
    # Net interconnections between instantiated components.
    #===============================================================================

    Net('+5V').connect(J1['1'], J2['3'], RV1['1'], U1['8'])

    Net('GND').connect(J1['5'], J2['1'], RV1['3'], U1['4'])

    Net('SERVO').connect(J2['2'], U1['7'])

    Net('V-POT').connect(RV1['2'], U1['2'])

    Net('unconnected-(J1-Pin_2-Pad2)').connect(J1['2'])

    Net('unconnected-(J1-Pin_3-Pad3)').connect(J1['3'])

    Net('unconnected-(J1-Pin_4-Pad4)').connect(J1['4'])

    Net('unconnected-(U1-AREF{slash}PB0-Pad5)').connect(U1['5'])

    Net('unconnected-(U1-PB1-Pad6)').connect(U1['6'])

    Net('unconnected-(U1-XTAL2{slash}PB4-Pad3)').connect(U1['3'])

    Net('unconnected-(U1-~{RESET}{slash}PB5-Pad1)').connect(U1['1'])


#===============================================================================
# Instantiate the circuit and generate the netlist.
#===============================================================================

if __name__ == "__main__":
    L___home__harriman__Projects__Elecroplating_Stirrer__EE__servo_control_module__servo_control_module_kicad_sch()
    generate_netlist()
