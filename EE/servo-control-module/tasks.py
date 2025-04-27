from invoke import task, context
from pathlib import Path
import sys


@task
def clean(ctx: context.Context) -> None:
    """
    Clean the project by removing all generated artifacts.
    """

    # List of extensions to clean
    extensions = [
        "svg",  # Graphic images for laser.
        "gbr",  # Gerbers
        "erc",  # Electrical rules check files
        "log",  # Logs
        "drl",  # Drill files
        "erx",  # KiCAD rules check files
        "xml",  # XML.  Created by kicad.py
        "ngc",  # G-Code
        "drl_cfg",  # Rendered drill config files
    ]

    for ext in extensions:
        files = Path().glob(f"*.{ext}")
        for file in files:
            file.unlink()

    # Panel files
    panel_files = Path().glob("panel.kicad_*")
    for file in panel_files:
        file.unlink()


def venv() -> bool:
    """
    Check if the virtual environment is active.

    Returns:
        bool: True if the virtual environment is active, False otherwise.
    """

    # Check if the virtual environment is active
    if "uv/python" in sys.base_prefix:
        return True
    else:
        return False


def board_find() -> Path:
    """
    Find the KiCAD PCB file in the current directory.

    Raises:
        ValueError: If no KiCAD PCB file is found.
        ValueError: If multiple KiCAD PCB files are found.
    """

    boards = list(Path().glob("*.kicad_pcb"))
    for board in boards:
        if board.name.startswith("panel"):
            # Skip panel files
            boards.remove(board)
    if len(boards) > 1:
        raise ValueError("Multiple KiCAD PCB files found.")

    if len(boards) == 0:
        raise ValueError("No KiCAD PCB file found.")

    return boards[0]


@task
def board(ctx: context.Context) -> None:
    """
    Lists name of default project board file.
    """

    board = board_find()

    print(f"Project board file: {board}", flush=True)


@task
def panelize(ctx: context.Context, board: str = None) -> None:
    """
    Panelize the PCB using KiKit.
    """

    if board is None:
        # Find the KiCAD PCB file in the current directory
        board = board_find()

    if not isinstance(board, Path):
        board = Path(board)

    if not board.exists():
        raise ValueError(f"Board file {board} does not exist.")

    # Run the panelizer script
    ctx.run(f"kikit panelize -p panel.json {board.name} panel.kicad_pcb")


@task
def drill(ctx: context.Context, board: str = None) -> None:
    """
    Generate drill files for the PCB.
    """

    if not venv():
        raise ValueError("uv virtual environment must be activated.  Try >>. venv")

    from kicad import PCB
    from string import Template

    if board is None:
        # Find the KiCAD PCB file in the current directory
        board = board_find()

    if not isinstance(board, Path):
        board = Path(board)

    if not board.exists():
        raise ValueError(f"Board file {board} does not exist.")

    # -------------------------------------------------------------------
    # Generate the drill files
    # -------------------------------------------------------------------
    pcb = PCB(board)
    drill_file, _ = pcb.drill()
    drill_file = Path(drill_file)
    if not drill_file.exists():
        raise ValueError(f"Drill file {drill_file} file generation error.")

    # -------------------------------------------------------------------
    # Generate G-code from the drill files.
    # -------------------------------------------------------------------

    # 1) Render the drill config template with the proper file name.
    drl_cfg = Path("cnc-drill.config")
    if not drl_cfg.exists():
        raise ValueError(f"Drill config file {drl_cfg} does not exist.")

    # Load the drill config temmplate and save rendered template.
    with open(drl_cfg, "r") as f:
        drl_cfg = f.read()

    drl_cfg = Template(drl_cfg)
    drl_fn = str(board.with_suffix(".drl"))
    drl_cfg = drl_cfg.substitute(file=drl_fn)

    drl_cfg_file = board.with_suffix(".drl_cfg")
    with open(drl_cfg_file, "w") as f:
        f.write(drl_cfg)

    # 2) Call pcb2gcode to generate the G-code.
    cmd = f"pcb2gcode --config=cnc-common.config,{drl_cfg_file} --drill {drl_fn} --basename {board.stem}"
    ctx.run(cmd)
    drl_cfg_file.unlink()  # Remove used rendered template file


@task
def process(ctx: context.Context, board: str = None) -> None:
    """
    Process the PCB file generating all fabrication files.
    """

    if board is None:
        # Find the KiCAD PCB file in the current directory
        board = board_find()

    if not isinstance(board, Path):
        board = Path(board)

    if not board.exists():
        raise ValueError(f"Board file {board} does not exist.")

    # Process steps
    print(f"Processing: {board}", flush=True)

    # Panelize the PCB
    print("\tpanelizing...", end="", flush=True)
    panelize(ctx, board)
    print(" done", flush=True)

    # Process complete
    print("Processing complete", flush=True)
