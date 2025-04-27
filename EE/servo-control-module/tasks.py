from invoke import task, context
from pathlib import Path
import re
import sys


# Silence warnings from gerbonara
if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")


@task
def clean(ctx: context.Context) -> None:
    """
    Clean the project by removing all generated artifacts.
    """

    # List of extensions to clean
    extensions = [
        "svg",  # Graphic images for laser.
        "gbr",  # Gerbers
        "gbrjob",  # Gerber job files
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


def pyver() -> bool:
    """
    Checks Python version for >= 3.11.

    Returns:
        bool: True if version is new enough.
    """

    vinfo = sys.version_info
    if vinfo.major < 3 or (vinfo.major == 3 and vinfo.minor < 11):
        return False

    return True


def board_find(board: str = None) -> Path:
    """
    Find the KiCAD PCB file in the current directory.

    Raises:
        ValueError: If no KiCAD PCB file is found.
        ValueError: If multiple KiCAD PCB files are found.
    """

    if board:
        if isinstance(board, str):
            board = Path(board)
        if not board.exists():
            raise ValueError(f"Board file {board} does not exist.")
        return board

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


def drill_file_split(file: Path) -> None:
    """
    Split the drill file into separate files, one for each bit.
    """

    if not isinstance(file, Path):
        raise TypeError(f"File must be a Path object, got: {type(file)}")
    if not file.exists():
        raise ValueError(f"File {file} does not exist.")

    # Read the file content
    with open(file, "r") as fp:
        lines = fp.readlines()

    # Extract bit sizes from the "Bit sizes" line
    bit_sizes_line = next(line for line in lines if "Bit sizes" in line)
    bit_sizes = re.findall(r"\[([\d.]+mm)\]", bit_sizes_line)

    # Find the header (everything before the first T<N> line)
    header = []
    for line in lines:
        if re.match(r"T\d+", line.strip()):
            break
        header.append(line)

    # Split the file into sections based on T<N> and "(Retract)"
    sections = {}
    current_tool = None
    current_section = []

    for line in lines:
        if re.match(r"T\d+", line.strip()):  # Start of a new tool section
            if current_tool is not None:
                sections[current_tool] = current_section
            current_tool = line.strip()
            current_section = [line]
        elif "retract" in line.lower():  # End of a tool section
            if current_tool is not None:
                current_section.append(line)
                sections[current_tool] = current_section
                current_tool = None
                current_section = []
        elif current_tool is not None:
            current_section.append(line)

    # Create new files for each bit size
    bit_idx = 0
    for tool in sections:
        bit_size = bit_sizes[bit_idx]
        bit_idx += 1
        output_file = Path(f"{file.stem}_{bit_size}.ngc")
        with open(output_file, "w") as out_file:
            # Write the header
            out_file.writelines(header)
            # Write the corresponding section for the tool
            out_file.writelines(sections[tool])


@task
def board(ctx: context.Context) -> None:
    """
    Lists name of default project board file.
    """

    board = board_find()

    print(f"Project board file: {board}", flush=True)


@task
def panelize(ctx: context.Context, board: str = None) -> Path:
    """
    Panelize the PCB using KiKit.
    """

    board = board_find(board)

    # Run the panelizer script
    panel_pcb = Path("panel.kicad_pcb")
    ctx.run(f"kikit panelize -p panel.json {board.name} {panel_pcb}")

    return panel_pcb


@task
def drills(ctx: context.Context, board: str = None) -> None:
    """
    Generates list of drill diameters in the PCB.
    """

    if not pyver():
        raise ValueError("Python too old.  Try >>. venv")

    board = board_find(board)

    # -------------------------------------------------------------------
    # Generate the Excelon drill file
    # -------------------------------------------------------------------
    from kicad import PCB

    pcb = PCB(board)
    drill_file, data = pcb.drill()
    drill_file.unlink()  # Remove drill file

    # Print list of drill diameters
    print(f"\n'{board.name}' specified drill diameters:")
    for drill in data.drill_sizes():
        print(f"\t{drill} [mm]")


@task
def drill(ctx: context.Context, board: str = None) -> None:
    """
    Generate CNC drill files for the PCB.
    """

    # if not venv():
    #     raise ValueError("uv virtual environment must be activated.  Try >>. venv")

    board = board_find(board)

    from kicad import PCB
    from string import Template

    # -------------------------------------------------------------------
    # Generate the Excelon drill file
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
    # cmd = f"pcb2gcode --config=cnc-common.config,{drl_cfg_file} --drill {drl_fn} --basename {board.stem}"
    cmd = (
        f"pcb2gcode --config=cnc-common.config,{drl_cfg_file}  --basename {board.stem}"
    )
    cmd += " > /dev/null 2>&1"
    ctx.run(cmd)
    drl_cfg_file.unlink()  # Remove used rendered template file

    # -------------------------------------------------------------------
    # Split G-code into separate files, one per drill size.
    # -------------------------------------------------------------------
    drill_nc_file = Path(f"{board.stem}_drill.ngc")
    drill_file_split(drill_nc_file)
    drill_nc_file.unlink()  # Remove G-code file


@task
def edgecut(ctx: context.Context, board: str = None) -> None:
    """
    Generates CNC edge cut out files for the PCB.
    """

    board = board_find(board)

    from kicad import PCB
    from string import Template

    # -------------------------------------------------------------------
    # Generate gerbers.
    # -------------------------------------------------------------------
    pcb = PCB(board)
    gbr_file = pcb.edge_cuts()

    # -------------------------------------------------------------------
    # Generate G-code from the Gerber file.
    # -------------------------------------------------------------------

    # 1) Render the drill config template with the proper file name.
    edge_cfg = Path("cnc-edge.config")
    if not edge_cfg.exists():
        raise ValueError(f"Edge cut config file {edge_cfg} does not exist.")

    # Load the drill config temmplate and save rendered template.
    with open(edge_cfg, "r") as f:
        edge_cfg = f.read()

    edge_cfg = Template(edge_cfg)
    drl_fn = board.stem + "-Edge_Cuts.gbr"
    edge_cfg = edge_cfg.substitute(file=drl_fn)

    edge_cfg_file = board.with_suffix(".edge_cfg")
    with open(edge_cfg_file, "w") as f:
        f.write(edge_cfg)

    # 2) Call pcb2gcode to generate the G-code.
    cmd = (
        f"pcb2gcode --config=cnc-common.config,{edge_cfg_file} --basename {board.stem}"
    )
    cmd += " > /dev/null 2>&1"
    ctx.run(cmd)

    # Remove intermedate files
    edge_cfg_file.unlink()
    gbr_file.unlink()


@task
def process(ctx: context.Context, board: str = None) -> None:
    """
    Process the PCB file generating all fabrication files.
    """

    board = board_find(board)

    # Process steps
    print(f"Processing: {board}", flush=True)

    # Panelize the PCB
    print("\tpanelizing...", end="", flush=True)
    panel_pcb = panelize(ctx, board)
    print("done", flush=True)

    # Generate drill files
    print("\tdrilling...", end="", flush=True)
    drill(ctx, panel_pcb)
    print("done", flush=True)

    # Generate edge cut files
    print("\tedge cutting...", end="", flush=True)
    edgecut(ctx, panel_pcb)
    print("done", flush=True)

    # Lots of intermediate SVG files are created.
    intermediate_files = [
        "original_drill.svg",
        "outp0_original_outline.svg",
        "processed_outline.svg",
        "traced_outline.svg",
    ]
    for file in intermediate_files:
        file = Path(file)
        if file.exists():
            file.unlink()

    # Process complete
    print("Processing complete", flush=True)


if __name__ == "__main__":
    from invoke import context

    drill(context.Context())
