from invoke import task, Context
import typing
from tasks_doc import *
from rich import print
from usbtiny import USBTiny


@task
def devices(ctx: Context):
    """
    List USB devices
    """

    print(USBTiny().table)


@task
def connect(ctx: Context, quiet: bool = False):
    """
    Attach USBtiny device to WSL USB.
    """
    from usbtiny import USBTiny

    usbtiny = USBTiny()

    # UI
    if not quiet:
        status = usbtiny.status
        print("[yellow]USBtiny device found:[yellow]")
        print(f"  State : {status['STATE']}")
        print(f"  Bus ID: {status['BUSID']}")

    if usbtiny.is_attached:
        if not quiet:
            print("  [yellow]Device already attached[/yellow]")
        return

    # Make connection
    if not usbtiny.attach():
        print("")
        print("[bold red]Connection Failed[/bold red]")
        print("   [yellow]Open Windows PowerSheel as Administrator and run:[/yellow]")
        print(f'   usbipd.exe wsl attach --busid {status["BUSID"]}')


@task
def clean(ctx: Context):
    """
    Clean build files.
    """

    types = ["o", "elf", "hex"]  # Build output
    types.append("vcd")  # Simulation output
    for t in types:
        ctx.run("rm -rf *." + t, echo=True)


@task
def flash(ctx: Context):
    """
    Flashes application binary to device.
    """

    # Check for application binary.
    if not os.path.isfile("main.hex"):
        make(ctx)

    # Check for connection.
    usbtiny = USBTiny()

    # Check for device
    if not usbtiny.is_attached:
        print("[bold red]Device not attached[/bold red]")
        print("   [yellow]Open Windows PowerSheel as Administrator and run:[/yellow]")
        print(f'   usbipd.exe wsl attach --busid {usbtiny.status["BUSID"]}')
        return

    # Flash
    ctx.run(f"sudo avrdude -c usbtiny -p attiny85 -U flash:w:main.hex:i", echo=True)


@task
def sim_debug(ctx: Context):
    """
    Run SIMAVR simulation.
    """

    binary = "sim.elf"

    # Check for application binary.
    if not os.path.isfile(binary):
        make_sim(ctx)

    # Run simulation
    print("[yellow bold]Simulator Started[/yellow bold]")
    print("  Run VSCode debugger to connect.")
    print("  CTRL-C to exit.")

    ctx.run(f"simavr -g -m attiny85 {binary}", echo=True)


@task
def sim_output(ctx: Context):
    """
    Run simulation generating VCD output file.
    """

    print("[bold red]Not Implemented Yet[/bold red]")

    # TODO: Run same as sim_debug, but no '-g' flag.
    # That will run the binary, and when it exits, dump a VCD file.
    # TODO: Set application up so it will exit after a few seconds.


@task
def make_sim(ctx: Context):
    """
    Compile simulation target.
    """
    make(ctx, target="sim", cflags="-DSIMULATION")


@task
def make(
    ctx: Context, target: str = "main", cflags: typing.Union[str, typing.List[str]] = []
):
    """
    Compile device target.
    """

    # TODO: Set up application build data so that other functions can access it.
    # TODO: Use doc_pre() to detrmine if we need to execute a step.

    from glob import glob

    # Read in makefile
    with open("makefile", "r") as fp:
        make = fp.read()
    lines = make.split("\n")

    compiler = "avr-gcc"
    F_CPU = int(1e6)
    DEVICE = "attiny85"

    if not isinstance(cflags, list):
        cflags = [cflags]

    cflags.append(f"-DF_CPU={F_CPU}")
    cflags.append(f"-mmcu={DEVICE}")
    cflags.append(f'-DDEVICE=\\"{DEVICE}\\"')
    cflags.append("-g")
    cflags.append("-Os")
    cflags.append("-Wall")
    cflags.append("-Werror")

    # CFLAGS to string
    cflags = " ".join(cflags)

    # Build the C files
    src = glob("*.c")
    obj = [file.replace(".c", ".o") for file in src]

    for srcfile, objfile in zip(src, obj):
        cmd = f"{compiler} {cflags} -c {srcfile} -o {objfile}"
        ctx.run(cmd, echo=True)

    # Link the objects
    cmd = f"{compiler} {cflags} -o {target}.elf {' '.join(obj)}"
    ctx.run(cmd, echo=True)

    # Flashable file
    cmd = f"avr-objcopy -j .text -j .data -O ihex {target}.elf  {target}.hex"
    ctx.run(cmd, echo=True)

    # Size info
    print("")
    cmd = f"avr-size --format=avr --mcu={DEVICE} {target}.elf"
    ctx.run(cmd, echo=False)
