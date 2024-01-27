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

## Soldermask & Silkscreen

Intended process is to apply two layers of soldermask/ink to the PCB, then use my UV laser to ablate the areas that I don't want filled in.  Overall technique from: https://www.youtube.com/watch?v=NuJlgw7E7vg.  Essentially:

1. Lay down & cure the base soldermask (color of choice)
2. Ablate soldermask in areas where you want silkscreen.
3. Apply white ink/soldermask & cure
4. Ablate solder pads.

### Software Tooling

While FlatCAM is a very impressive piece of Python GUI software, it's cumbersome to have to do a lot of manual stuff.  Per above, `PCB2GCODE` does a great job with the isolation routing, edge routing and drilling G-code file generation.  Once you've properly parameterized your system, it's a two second opeation to go from Gerber to G-Code.  Looking to add in the next steps in that tooling for laser ablation paths.

We need to go from Gerber to G-Code. [Gerbonara](https://gerbolyze.gitlab.io/gerbonara/#) can read Gerber files and provide graphics primitives which can be converted to G-Code by a custom Python module `gbr2grbl.py`.  This is able to draw and fill rectangles and circles, which meets the most basic of soldermask needs.

With a "dumb" implementaiton, just generating G-code geometry,
* With 0.1mm infill step size, CAMotics estimates:
    * Job time: 1m 21s
    * Total distance: 1378.1 mm.
* No infill
    * Job time: 15s
    * Total distance: 239.2 mm.

With 2D position scheduling optimization
* With 0.1mm infill step size, CAMotics estimates:
    * Job time: 1m 18s (3.7% savings)
    * Total distance: 778.0mm (43.5% savings)
* With no infille, CAMotics estimates:
    * Job time: 14.9s (0.7% savings)
    * Total distance: 222.1mm (7.1% savings)


To do:

- Looks like need to flip bottom side image.
- Verify home position is correct.
- Add in laser G-code parameters as TOML config file.
- Add generation of other g-code files handled by `pcb2gcode` (drill, edge route, isolation route).
- Parameterize `pcb2gcode` to use the same TOML config file.
- Use `.gbrjob` data for `pcb2gcode` config.  Stackup has PCB and Cu thicknesses.
- Make sure I have the stackup config correct in the KiCAD PCB file.

## Overall Process

Note: For all operations, keep grbl software running and maintain XY home position.

1. Mount bare PCB to a flat but sacrificial material which is clamped to the mill bed.  PCB mounting via glued tape attached to both surfaces.  Doublesided tape will work well also.
2. If the PCB is double sided, drill corner holes that can be fitted with dowell pins for locating.
3. Autolevel board
4. Isolation route PCB back side.  Start with back side to minimize flips (assuming silksceen is front side only).
5. If double sided: clean PCB apply and cure back side soldermask, flip board, repeat steps 3 & 4 for front side.
6. Clean PCB, apply & cure soldermask.
8. Mount laser.
9. Ablate silkscreen image.
10. Apply & cure silkscreen ink
11. Ablate soldermask for solder pads
12. Remount spindle
13. Drill
14. Edge route
15. Tin exposed pads.
