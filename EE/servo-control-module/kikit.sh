#!/usr/bin/bash

# "Panelize" PCB for home fab.

# Cleanup
rm -f panel.kicad_*

# Board file
BOARD=servo-control-module.kicad_pcb

# Program
# Running as the host system current user so that generated files are owned by the user
# not root.  This will throw some errors about inablity to create some config dirs when
# running, but those don't seem to matter.
#PROG="docker run -v $(pwd):/kikit -u $(id -u ${USER}):$(id -g ${USER}) --rm yaqwsx/kikit"
PROG="docker run -v $(pwd):/kikit -u $(id -u ${USER}):$(id -g ${USER}) --rm kikit/local-9"

# Run the panelization
$PROG panelize -p panel.json $BOARD panel.kicad_pcb