from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

SKIDL_lib_version = '0.0.1'

ipython_lib = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Conn_01x05_Pin', 'dest':TEMPLATE, 'tool':SKIDL, 'pin':None, 'do_erc':True, 'num_units':None, 'aliases':Alias({'Conn_01x05_Pin'}), 'description':'', 'footprint':':', 'reference':'J', '_match_pin_regex':False, 'ki_locked':'', 'keywords':'connector', 'ki_keywords':'connector', '_aliases':Alias({'Conn_01x05_Pin'}), 'ref_prefix':'J', 'fplist':[''], 'ki_fp_filters':'Connector*:*_1x??_*', 'orientation_locked':False, 'datasheet':'~', 'bbox':<class 'skidl.schematics.geometry.BBox'>(Point((inf, inf)), Point((-inf, -inf))), '_name':'Conn_01x05_Pin', 'tx':<class 'skidl.schematics.geometry.Tx'>(1, 0, 0, 1, 0, 0), 'num':1, 'pins':[
            Pin(num='1',name='Pin_1',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='2',name='Pin_2',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='3',name='Pin_3',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='4',name='Pin_4',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='5',name='Pin_5',func=Pin.types.PASSIVE,do_erc=True)] }),
        Part(**{ 'name':'Screw_Terminal_01x03', 'dest':TEMPLATE, 'tool':SKIDL, 'pin':None, 'do_erc':True, 'num_units':None, 'aliases':Alias({'Screw_Terminal_01x03'}), 'description':'', 'footprint':'TerminalBlock_TE-Connectivity:TerminalBlock_TE_282834-3_1x03_P2.54mm_Horizontal', 'reference':'J', '_match_pin_regex':False, 'ki_keywords':'screw terminal', 'keywords':'screw terminal', '_aliases':Alias({'Screw_Terminal_01x03'}), 'ref_prefix':'J', 'fplist':[''], 'ki_fp_filters':'TerminalBlock*:*', 'datasheet':'~', '_name':'Screw_Terminal_01x03', 'num':1, 'pins':[
            Pin(num='1',name='Pin_1',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='2',name='Pin_2',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='3',name='Pin_3',func=Pin.types.PASSIVE,do_erc=True)] }),
        Part(**{ 'name':'ATtiny25V-10P', 'dest':TEMPLATE, 'tool':SKIDL, 'pin':None, 'do_erc':True, 'num_units':None, 'aliases':Alias({'ATtiny85-20P', 'ATtiny25V-10P'}), 'description':'', 'footprint':'Package_DIP:DIP-8_W7.62mm', 'reference':'U', '_match_pin_regex':False, 'ki_keywords':'AVR 8bit Microcontroller tinyAVR', 'keywords':'AVR 8bit Microcontroller tinyAVR', '_aliases':Alias({'ATtiny85-20P', 'ATtiny25V-10P'}), 'ref_prefix':'U', 'fplist':['Package_DIP:DIP-8_W7.62mm', 'Package_DIP:DIP-8_W7.62mm'], 'ki_fp_filters':'DIP*W7.62mm*', 'datasheet':'http://ww1.microchip.com/downloads/en/DeviceDoc/atmel-2586-avr-8-bit-microcontroller-attiny25-attiny45-attiny85_datasheet.pdf', '_name':'ATtiny25V-10P', 'num':1, 'pins':[
            Pin(num='1',name='~{RESET}/PB5',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='2',name='XTAL1/PB3',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='3',name='XTAL2/PB4',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='4',name='GND',func=Pin.types.PWRIN,do_erc=True),
            Pin(num='5',name='AREF/PB0',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='6',name='PB1',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='7',name='PB2',func=Pin.types.BIDIR,do_erc=True),
            Pin(num='8',name='VCC',func=Pin.types.PWRIN,do_erc=True)] }),
        Part(**{ 'name':'R_Potentiometer', 'dest':TEMPLATE, 'tool':SKIDL, 'pin':None, 'do_erc':True, 'num_units':None, 'aliases':Alias({'R_Potentiometer'}), 'description':'', 'footprint':':', 'reference':'RV', '_match_pin_regex':False, 'ki_keywords':'resistor variable', 'keywords':'resistor variable', '_aliases':Alias({'R_Potentiometer'}), 'ref_prefix':'RV', 'fplist':[''], 'ki_fp_filters':'Potentiometer*', 'datasheet':'~', '_name':'R_Potentiometer', 'num':1, 'pins':[
            Pin(num='1',name='1',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='2',name='2',func=Pin.types.PASSIVE,do_erc=True),
            Pin(num='3',name='3',func=Pin.types.PASSIVE,do_erc=True)] })])