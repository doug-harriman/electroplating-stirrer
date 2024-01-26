# GBR2GRBL
# KiCAD Gerber to GRBL compliant G-Code converter.

import datetime as dt
import json
import logging
import os
from typing import Union

import gerbonara
import networkx as nx

import gcode_doc as gcd

# Configue logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(name)s:%(levelname)s - %(message)s",
    handlers=[logging.FileHandler("gbr2grbl.log"), logging.StreamHandler()],
)


class GerberJob:
    """
    Class for processing KiCAD '.gbrjob' files.
    """

    def __init__(self, filename: str = None) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

        self._filename = None
        self._project_name = None
        self._project_rev = None
        self._board_thickness = None
        self._layers = None

        if filename is not None:
            self.load(filename)

    @property
    def filename(self) -> Union[str, None]:
        """
        Returns the filename.

        Returns:
            str: Filename.
        """

        return self._filename

    @property
    def project_name(self) -> Union[str, None]:
        """
        Returns the project name.

        Returns:
            str: Project name.
        """

        return self._project_name

    @property
    def project_rev(self) -> Union[str, None]:
        """
        Returns the project revision.

        Returns:
            str: Project revision.
        """

        return self._project_rev

    @property
    def board_thickness(self) -> Union[float, None]:
        """
        Returns the board thickness.

        Returns:
            float: Board thickness.
        """

        return self._board_thickness

    @property
    def layers(self) -> Union[dict, None]:
        """
        Returns the board layer stackup.

        Returns:
            dict: Board layer stackup keyed by layer name.
        """

        return self._layers

    def load(self, filename: str) -> None:
        """
        Load a KiCAD '.gbrjob' file.

        Args:
            filename (str): KiCAD '.gbrjob' file to load.
        """
        if not isinstance(filename, str):
            raise TypeError(f"filename must be a string, not {type(filename)}")
        if not filename.endswith(".gbrjob"):
            raise ValueError(f"filename must end with .gbrjob, not {filename}")
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        self._filename = filename

        with open(filename, "r") as fp:
            self.data = json.load(fp)

        self._project_name = self.data["GeneralSpecs"]["ProjectId"]["Name"]
        self._project_rev = self.data["GeneralSpecs"]["ProjectId"]["Revision"]
        if self._project_rev == "rev?":
            self._project_rev = None
        self._logger.debug(f"Project: {self.project_name}, rev: {self.project_rev}")

        # Only 1 and 2 layer boards supported
        layers = self.data["GeneralSpecs"]["LayerNumber"]
        if layers not in [1, 2]:
            logging.error(f"Board layer count={layers}, only 1 and 2 supported")
            raise ValueError(f"Only 1 and 2 layer boards supported")

        # Board thickness
        self._board_thickness = self.data["GeneralSpecs"]["BoardThickness"]

        # Verify we can find the files.
        for i, fileattr in enumerate(self.data["FilesAttributes"]):
            if not os.path.isfile(fileattr["Path"]):
                self._logger.warning(f"File not found: {fileattr['Path']}")

                # Null it out
                self.data["FilesAttributes"][i] = None

        # Remove any nulls
        self.data["FilesAttributes"] = [
            x for x in self.data["FilesAttributes"] if x is not None
        ]

        # Verify we have at least one file.
        if len(self.data["FilesAttributes"]) == 0:
            raise ValueError(f"No valid files found in {filename}")

        for fileattr in self.data["FilesAttributes"]:
            self._logger.debug("Gerber file found: " + fileattr["Path"])

        # Process board material stackup.
        self._layers = {}
        for layer in self.data["MaterialStackup"]:
            thickness = None
            if "Thickness" in layer:
                thickness = layer["Thickness"]

            self._layers[layer["Name"]] = thickness

    def silkscreen(self) -> list:
        """
        Returns the names and polarities of the silk screen layers.

        Returns:
            list: List of silk screen layer files.
        """

        silk = []
        for fileattr in self.data["FilesAttributes"]:
            if "_Silkscreen" in fileattr["Path"]:
                d = {}
                d["Path"] = fileattr["Path"]
                d["Polarity"] = fileattr["FilePolarity"]
                silk.append(d)

        return silk

    def mask(self) -> list:
        """
        Returns the names and polarities of the solder mask layers.

        Returns:
            list: List of solder mask layer files.
        """

        mask = []
        for fileattr in self.data["FilesAttributes"]:
            if "_Mask" in fileattr["Path"]:
                d = {}
                d["Path"] = fileattr["Path"]
                d["Polarity"] = fileattr["FilePolarity"]
                mask.append(d)

        return mask

    def to_gcode(self):
        """
        Converts all Gerber files the GerberJob to G-Code.
        """

        # Process files by type.
        # silks = self.silkscreen()
        # for silk in silks:
        #     self._logger.debug(f"Silkscreen: {silk['Path']}")
        #     g2g = Gerber2Gcode(silk["Path"], silk["Polarity"])
        #     g2g.to_gcode()

        masks = self.mask()
        for mask in masks:
            self._logger.debug(f"Mask: {mask['Path']}")
            g2g = Gerber2Gcode(mask["Path"], mask["Polarity"])
            g2g.to_gcode()


class Gerber2Gcode:
    def __init__(self, filename: str, polarity: str) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gcode_extension = ".gcode"
        self._polarity = None
        self._gerber = None

        if filename is not None:
            self.load(filename, polarity)

    @property
    def filename(self) -> Union[str, None]:
        """
        Returns the filename.

        Returns:
            str: Filename.
        """

        return self._filename

    @property
    def polarity(self) -> Union[str, None]:
        """
        Returns the polarity.

        Returns:
            str: Polarity.
        """

        return self._polarity

    def load(self, filename: str, polarity: str) -> None:
        """
        Load a Gerber file.

        Args:
            filename (str): Gerber file to load.
            polarity (str): Gerber file polarity.
        """
        if not isinstance(filename, str):
            raise TypeError(f"filename must be a string, not {type(filename)}")
        if not filename.endswith(".gbr"):
            raise ValueError(f"filename must end with .gbr, not {filename}")
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        self._filename = filename

        if not isinstance(polarity, str):
            raise TypeError(f"polarity must be a string, not {type(polarity)}")
        polarity = polarity.lower()
        if polarity not in ["positive", "negative"]:
            raise ValueError(f"polarity must be positive or negative, not {polarity}")
        self._polarity = polarity

        # Load the Gerber file.
        try:
            self._gerber = gerbonara.GerberFile.open(filename)
        except Exception as e:
            self._logger.error(f"Error loading {filename}: {e}")
            raise

        self._gcode_filename = (
            os.path.splitext(os.path.basename(self.filename))[0] + self._gcode_extension
        )

        self._logger.debug(f"Gerber file found: {self.filename}")
        self._logger.debug(f"Gerber file polarity: {self.polarity}")

    def to_svg(self, filename: Union[str, None] = None) -> str:
        """
        Converts the Gerber file to SVG.

        Args:
            filename (str): SVG file name.  Defaults to Grber file name with .svg extension.

        Returns:
            str: SVG file name as a string.
        """

        if not self._gerber:
            logging.error("No Gerber file loaded")
            raise ValueError("No Gerber file loaded")

        # SVG file name
        if filename is None:
            filename = os.path.splitext(os.path.basename(self.filename))[0] + ".svg"
        else:
            if not isinstance(filename, str):
                raise TypeError(f"filename must be a string, not {type(filename)}")
            if not filename.endswith(".svg"):
                raise ValueError(f"filename must end with .svg, not {filename}")

        self._logger.debug(f"Generating SVG file: {filename}")

        data = self._gerber.to_svg(fg="black", bg="white")
        svg_str = str(data)

        # Write the SVG file.
        with open(filename, "w") as fp:
            fp.write(svg_str)

        return filename

    def to_gcode(self, filename: Union[str, None] = None) -> str:
        """
        Converts the Gerber file to G-Code.

        Args:
            filename (str): G-Code file name.  Defaults to Grber file name with .gcode extension.

        Returns:
            str: G-Code file name as a string.
        """

        # G-Code file name
        if filename is None:
            if self.filename is None:
                raise ValueError("No Gerber file loaded")
            filename = (
                os.path.splitext(os.path.basename(self.filename))[0]
                + self._gcode_extension
            )
        else:
            if not isinstance(filename, str):
                msg = f"filename must be a string, not {type(filename)}"
                self._logger.error(msg)
                raise TypeError(msg)

        if self._gerber is None:
            msg = "No Gerber file loaded"
            self._logger.error(msg)
            raise ValueError(msg)

        # Rectangle: x,y is center coord.
        # TODO: Need to support translation & rotation of my G-code objects
        # TODO: Need to support generating infill passes for my g-code objects.

        # G-code document
        doc = gcd.Doc()
        doc.layout = gcd.GraphLayout()

        # Process Gerber geometry objects.
        for obj in self._gerber.objects:
            shape = None
            prim = list(obj.to_primitives())[0]

            # Line objects with no length are circles, override those.
            if isinstance(prim, gerbonara.graphic_primitives.Line):
                if prim.x1 == prim.x2 and prim.y1 == prim.y2:
                    prim = gerbonara.graphic_primitives.Circle(
                        prim.x1, prim.y1, prim.width / 2
                    )

            self._logger.debug(f"{prim}")
            if isinstance(prim, gerbonara.graphic_primitives.Rectangle):
                shape = gcd.Rectangle(
                    prim.x,
                    prim.y,
                    prim.w,
                    prim.h,
                    prim.rotation,
                )

            elif isinstance(prim, gerbonara.graphic_primitives.Line):
                self._logger.error("Line primitive not supported")
            elif isinstance(prim, gerbonara.graphic_primitives.Circle):
                self._logger.error("Circle primitive not supported")
            elif isinstance(prim, gerbonara.graphic_primitives.Arc):
                self._logger.error("Arc primitive not supported")
            elif isinstance(prim, gerbonara.graphic_primitives.ArcPoly):
                self._logger.error("ArcPoly primitive not supported")
            else:
                msg = f"Unsupported primitive: {type(prim)}"
                self._logger.warning(msg)
                raise ValueError(msg)

            # Add the shape to the document.
            if shape:
                doc.AddChild(shape)

        # Write the G-Code file.
        doc.GCode(filename)

        return filename


if __name__ == "__main__":
    # import sys

    # if len(sys.argv) < 2:
    #     print("Usage: gbr2grbl.py <gbrjob file>")
    #     sys.exit(1)
    # gbrjob = GerberJob()
    # gbrjob.load(sys.argv[1])

    filename = "servo-control-module-job.gbrjob"
    gbrjob = GerberJob()
    gbrjob.load(filename=filename)
    gbrjob.to_gcode()
