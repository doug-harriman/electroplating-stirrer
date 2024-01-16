# PCB Milling

[Good overall resource](https://hobbycnc.com/pc_board_isolation_routing/pc-board-isolation-routing-kicad/)

## KiCAD

KiCAD Gerber export: disable the "Use extended X2 format" option.

## PCB2GCODE

* This tool worked great for generating G-code.
    * Much easier to use than FlatCAM.
    * Man page in file `pcb2gcode.pdf`.
* Example config file: `millproject`
* Generate code by running `pcb2gcode` in the same directory with `millproject`.
* Use a short list of drill sizes, or it will use exact drill size for each part.  That can lead to a lot of tooling changes.
* You can get some parameter by editing and running `pcb_calcs.py`.
    * The copper layer is very thin.  Got nice isolation with a margin of 0.5, could probably go lower.
    * This calcs the Z depth for drilling and edge cuts to cut into the tape.  It can be a bit tricky if you don't apply the height map.  Not clear if you can apply the height map to multiple files.
* Bridges shouldn't be necessary if you don't cut too fast on the edge cuts.

## Mounting PCB

It is *very* important to get the board as flat as possible.  The painters tape glued together does seem to work well if:
* Mounted to the aluminum plate, not the MDF spoilboard.
* Clean the aluminum with isopropal alcolhol ahead of time so tape adheres well.
* While glue is drying, put a large weight on the PCB.  A 5 lb sledge hammer worked well.

## Tooling

The 60 degree triangular V-cut bits worked very well.  Robust bit, and isolated nicely.
* [Inventree](http://192.168.0.120:8800/part/48/)
* [Amazon](https://www.amazon.com/gp/product/B08881PKBN?th=1)

## Autoleveling

* Use CNCjs autolevel module: https://github.com/kreso-t/cncjs-kt-ext
    * This is loaded on the Shop Server, in the CNCjs VM.
    * It's in directory `~/tmp/cncjs-kt-ext/`
    * It must be restarted every time the USB connection is made.
        * `>> node . --port /dev/ttyUSB0`
    * Create a macro or run from the command line:
        * `(#autolevel D7.5 H1.0 F20)`
        * `F` - Z-probe speed, don't go lower than 20 (mm/sec).
        * `D` - Grid spacing.  Defaults to 10 (mm).

