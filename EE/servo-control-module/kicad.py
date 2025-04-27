# kicad.py
# Python module interface to KiCad 8's CLI kicad-cli

# Python standard modules
from pathlib import Path
import tempfile
import json
import xml.etree.ElementTree as ET
import re

# pip installed modules
import sh
import gerbonara
from kinparse import parse_netlist
from pyparsing.results import ParseResults


class SCH:
    """KiCad 8 Schematic CLI interface"""

    def __init__(self, file: str | Path = None) -> None:
        # Store the command.
        self._run = sh.Command("kicad-cli").bake("sch")

        self._file = None
        if file:
            self.file = file

    @property
    def file(self) -> str:
        """
        KiCad PCB file name.
        If set with a non-existent '.kicad_pcb' extension, will substitute that exension.
        """

        return self._file

    @file.setter
    def file(self, value: str | Path):
        if not isinstance(value, str) and not isinstance(value, Path):
            raise TypeError(
                f"KiCad schematic file: expected str or Path, got: {type(value)}"
            )

        # Substitute the extension if needed
        if not isinstance(value, Path):
            value = Path(value)
        value = value.with_suffix(".kicad_sch")

        if not value.is_file():
            raise FileNotFoundError(f"KiCad schematic file not found: {value}")

        self._file = value

    @property
    def version(self) -> str:
        """
        KiCad version.
        """

        # Run command
        version = sh.Command("kicad-cli")("--version").strip()

        # Return all
        return version

    def netlist(self) -> ParseResults:
        """
        Generate a netlist from the KiCad schematic file.

        Returns:
        - pyparsing.results.ParseResults: Netlist data.  See: https://devbisme.github.io/kinparse/docs/_build/singlehtml/index.html#document-usage
        """

        if not self.file:
            raise ValueError("KiCad schematic file not set")

        # Run command
        outfile = self.file.with_suffix(".net")
        self._run("export", "netlist", self.file)

        # Load results
        netlist = parse_netlist(outfile)

        # Return all
        return outfile, netlist

    def to_pdf(self, vars: dict = None) -> str:
        """
        Generate a PDF from the KiCad schematic file.

        Args:
        - vars (dict): Add or override project variable definitions. Default = None.

        Returns:
        - str: Path to the PDF file.
        """

        if not self.file:
            raise ValueError("KiCad schematic file not set")

        # TODO: Test this, it is untested.  May need comma between variable definitions.
        args = None
        if vars and not isinstance(vars, dict):
            raise TypeError(f"vars: expected dict, got: {type(vars)}")
        if vars:
            args = ["-D "]
            for k, v in vars.items():
                args += [f"{k}={v}"]

        # Run command
        outfile = self.file.with_suffix(".pdf")
        self._run("export", "pdf", args, self.file)

        # Return all
        return outfile


class PCB:
    """KiCad 8 PCB CLI interface"""

    def __init__(self, file: str | Path = None) -> None:
        # Store the command.
        self._run = sh.Command("kicad-cli").bake("pcb")

        self._file = None
        if file:
            self.file = file

    @property
    def file(self) -> str:
        """
        KiCad PCB file name.
        If set with a non-existent '.kicad_pcb' extension, will substitute that exension.
        """

        return self._file

    @file.setter
    def file(self, value: str | Path) -> None:
        if not isinstance(value, str) and not isinstance(value, Path):
            raise TypeError(f"KiCad PCB file: expected str or Path, got: {type(value)}")

        # Substitute the extension if needed
        if not isinstance(value, Path):
            value = Path(value)
        value = value.with_suffix(".kicad_pcb")

        if not value.is_file():
            raise FileNotFoundError(f"KiCad PCB file not found: {value}")

        self._file = value

    @property
    def version(self) -> str:
        """
        KiCad version.
        """

        # Run command
        version = sh.Command("kicad-cli")("--version").strip()

        # Return all
        return version

    @property
    def layers(self) -> list:
        """
        Returns list of active layers in PCB file.
        Generates IPC-2581 output file, then parses for active layers.
        """

        if not self.file:
            raise ValueError("KiCad PCB file not set")

        # Run command
        outfile = self.file.with_suffix(".xml")
        self._run("export", "ipc2581", self.file)

        # Load results
        tree = ET.parse(outfile)

        # Find all LayerRef elements
        # When parsed, the namespace is expanded per teh xmlns link.
        layer_refs = tree.findall(".//{http://webstds.ipc.org/2581}LayerRef")

        # Extract name values
        layers = [
            layer_ref.get("name").replace("LAYER:", "") for layer_ref in layer_refs
        ]

        # Drop the dialetric layers
        layers = [name for name in layers if not name.startswith("DIELECTRIC")]

        return layers

    def edge_cuts(self) -> Path:
        """
        Generates Edge Cut Gerber.
        """

        # Command line arguments
        params = {
            "--layers": "Edge.Cuts",
        }
        options = ["--no-netlist", "--use-drill-file-origin", "--no-protel-ext"]

        args = ""
        for param in params:
            args += f" {param}={params[param]}"
        for option in options:
            args += f" {option}"
        args += f" {self.file}"
        args = args.split()

        self._run.export("gerbers", *args)

        # Return output file
        outfile = Path(self.file.stem + "-Edge_Cuts.gbr")
        return outfile

    def drc(self) -> dict:
        """
        Run PCB design rules check (DRC) on the KiCad PCB file.

        Returns:
        - dict: DRC results as a dictionary.
        """

        if not self.file:
            raise ValueError("KiCad PCB file not set")

        args = []
        args += ["--format", "json"]
        args += ["--schematic-parity"]
        args += ["--severity-all"]

        # Run command and load results
        with tempfile.NamedTemporaryFile(delete=True) as temp:
            args += ["--output", temp.name]
            self._run("drc", args, self.file)

            # Read the results
            results = json.load(temp)

        return results

    def drill(
        self, mirror_y: bool = False, mapfile: bool = False
    ) -> tuple:  # [str, gerbonara.ExcellonFile]:
        """
        Generates drill data for the KiCad PCB file.

        Args:
        - mirror_y (bool): Mirror the Y axis.  Default = False.
        - mapfile (bool): Create a map file.  Default = False.

        Returns:
        - str: Path to the drill file.
        - gerbonara.ExcellonFile: Drill data. See: https://gerbolyze.gitlab.io/gerbonara/file-api.html#gerbonara.excellon.ExcellonFile
        """

        if not self.file:
            raise ValueError("KiCad PCB file not set")
        if not isinstance(mirror_y, bool):
            raise TypeError(f"mirror_y: expected bool, got: {type(mirror_y)}")
        if not isinstance(mapfile, bool):
            raise TypeError(f"mapfile: expected bool, got: {type(mapfile)}")

        # Handle defaults
        outfile = self.file.with_suffix(".drl")
        args = []
        args += ["--format", "excellon"]

        if mirror_y:
            args += ["--mirror-y"]
        if mapfile:
            args += ["--map-file", "pdf"]

        # Run command
        self._run("export", "drill", args, self.file)

        # Load results
        data = gerbonara.ExcellonFile.open(outfile)

        # Return all
        return outfile, data

    def gerbers(self, layers: list = None) -> list:
        """
        Generates Gerber for all specified layers in the KiCad PCB file.

        Args:
        - layers (list[str]): List of layers to generate.  Default = None (all layers).

        Returns:
        - list[Path]: List of generated Gerber files.
        """

        if not self.file:
            raise ValueError("KiCad PCB file not set")

        board_layers = self.layers
        requested_layers = layers
        if not layers:
            layers = board_layers
        else:
            layers = []
            for layer in requested_layers:
                if layer not in board_layers:
                    print(f"WARNING: requested layer not in PCB, skipping: {layer}")
                    continue
                layers.append(layer)

        layer_str = ""
        for layer in layers:
            layer_str += layer + ","
        layer_str = layer_str[:-1]
        args = ["--layers", layer_str]

        print(f"Exporting layers: {','.join(layers)}")

        # Run command
        res = self._run("export", "gerbers", args, self.file)

        # Find all generated file names
        files = re.findall(r"'(.*?)'", res)
        newfiles = []
        for file in files:
            file = Path(file)
            newfile = Path(file).with_suffix(".gbr")
            file.rename(newfile)
            newfiles.append(newfile)

        # Include the jobfile.
        jobfile = self.file.stem + "-job.gbrjob"
        newfiles.append(Path(jobfile))

        return newfiles


def clean():
    """
    Removes all KiCad module generated files.
    """

    # List all projects in the current directory
    projects = list(Path(".").glob("*.kicad_pro"))
    extensions = [
        ".drl",
        ".dxf",
        ".json",
        ".net",
        ".pdf",
        ".rpt",
        ".svg",
        ".pdf",
        ".wrl",
        ".step",
        ".xml",
        ".gbr",
        ".gbrjob",
    ]

    # Remove all files with the extensions
    for project in projects:
        for ext in extensions:
            file = project.with_suffix(ext)
            if file.is_file():
                file.unlink()

        # Gerbers have a modified filename
        gerbers = list(Path(".").glob(f"{project.stem}*.gbr"))
        for gerber in gerbers:
            gerber.unlink()

        gerber_job = list(Path(".").glob(f"{project.stem}*.gbrjob"))
        for job in gerber_job:
            job.unlink()


if __name__ == "__main__":
    fn = "servo-control-module.kicad_pcb"
    pcb = PCB(fn)
    f, d = pcb.drill()
