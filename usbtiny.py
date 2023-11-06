# Desc: USBtiny device class.
# Helper class to manage USBtiny device connection to WSL USB bus.

import sh
from io import StringIO
import pandas as pd


class USBTiny:
    def __init__(self):
        self._usbipd = sh.Command("usbipd.exe")
        self._table = None

    def update(self) -> None:
        """
        Updates device status, forcing read.

        Raises:
            RuntimeError: If USBtiny device not found on USB bus.
        """

        devices = self._usbipd("list")
        df = pd.read_table(
            StringIO(devices), engine="python", header=1, sep="\s{2,}", index_col=False
        )

        # Drop stuff below the main table.
        idx = df[df["BUSID"] == "Persisted:"].index.values[0]
        df.drop(df.index[idx:], inplace=True)

        self._table = df

    @property
    def status(self) -> dict:
        """
        Returns full device record for USBtiny device.

        Returns:
            dict: USBtiny device status record.
        """

        df = self.table
        try:
            device = df[df["DEVICE"] == "USBtiny"].to_dict(orient="records")[0]
        except KeyError:
            raise RuntimeError(
                "USBtiny device not found on USB bus, see 'usbipd.exe list'"
            )

        return device

    @property
    def table(self) -> pd.DataFrame:
        """
        USB device connection table.
        Accessing this property forces a table update.

        Returns:
            pandas.DataFrame: Table of USB device info.
        """

        if self._table is None:
            self.update()

        return self._table

    @property
    def is_attached(self) -> bool:
        """
        Checks if device is attached.

        Returns:
            bool: True if device is attached.
        """

        return self.status["STATE"] == "Attached"

    @property
    def busid(self) -> str:
        """
        Returns device USB bus ID.

        Returns:
            str: Bus ID.
        """

        return self.status["BUSID"]

    @property
    def vidpid(self) -> str:
        """
        Device VID:PID.

        Returns:
            str: VID:PID.
        """

        return self.status["VID:PID"]

    def attach(self) -> bool:
        """
        Attempts to attach device to WSL USB bus.

        Returns:
            bool: True if device attached.
        """

        try:
            sh.contrib.sudo(self._usbipd._path, "wsl", "attach", "--busid", self.busid)
            return True
        except sh.ErrorReturnCode_3:
            return False
