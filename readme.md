# Firmware

## Compiler

`sudo apt install make gcc-avr avr-libc avrdude`

## Programmer

* [Amazon](https://www.amazon.com/gp/product/B09X1W2TPG/)
* [SparkFun Docs](https://www.sparkfun.com/products/11801)

### WSL USB

Overview of [WSL USB access](https://learn.microsoft.com/en-us/windows/wsl/connect-usb).

1. Install the WSL drivers for your kernel.
    1. Open a WSL terminal and run `usbipd list`.  This will display packages that need to be installed for your WSL kernel.
    1. Install those packages.

1. Install the [programmer Windows driver](https://github.com/adafruit/Adafruit_Windows_Drivers/releases) & plug in the programmer.
   * Windows device manager should now show `libusb-win32 devices -> USBtiny`

1. Make the USB device available to WSL
    1. Open a WSL shell.
    1. List available USB devices: `usbipd.exe list`.  Find the `USBtiny` device and note the bus ID.
        * Note: This is calling a Windows executable from WSL.
    1. Attach the USB device to WSL: `usbipd.exe wsl attach --busid <bus ID>`.  The device should now be available in WSL.
        * When you're done with the device, detach with the command above, substituting `detach` for `attach`.
    1. Verify the device is available in an WSL terminal: `lsusb`.  The device should be listed.

1. Create a `udev` rules file to make the device accessible to `avrdude`.
    1. After attaching the device to WSL per above, run `lsusb` to get the `idVendor` and `idProduct` values needed next.  The output should look something like this:
        ```
        Bus 001 Device 002: ID 1781:0c9f Multiple Vendors USBtiny
        ```
        In this example (default for the usbtiny programmer), the `idVendor` is `1781` and the `idProduct` is `0c9f`.

    1. Create a file `/etc/udev/rules.d/99-usb.rules` with the following contents:
        ```
        SUBSYSTEM=="usb", ATTR{idVendor}=="1781", ATTR{idProduct}=="0c9f", MODE="0660", GROUP="plugdev"
        ```
        * The `idVendor` and `idProduct` values are from the output of `usbipd list` above.
    1. Add your user to the group.  This will require logging out and back in.
        ```
        sudo usermod -a -G plugdev $USER
        ```
    1. Reload the `udev` rules: `sudo udevadm control --reload-rules && sudo udevadm trigger`

    NOTE: If you're unable to access, try with `sudo` permissions.



https://devblogs.microsoft.com/commandline/connecting-usb-devices-to-wsl/

https://www.krekr.nl/content/using-usbtinyisp-with-ubuntu/
https://www.tonymitchell.ca/posts/programming-avr-in-wsl-tips-and-tricks/


## Simulator

[SimAVR](https://github.com/buserror/simavr)

`sudo apt install simavr`

also installs `gdb-avr` as a dependency.

To run a simulation, you need a special build that brings in simulator symbols.
See `main-sim.c`

`make sim`

If you run the simulator with the `-g` flag, it will open up a gdb server port.
You can then attach a GDB session to that port.

## Debugger

* VSCode launch target defined in `.vscode/launch.json`
* `make sim-debug` to build the debug target and lanch the gdb-avr server process.
    * Needs to be redone every code change.
    * Make sure to kill the debugger if you relaunch.
* Select the VSCode debug and run with the AVR Debug configuration.

# Electronics

## AtTiny85

[Amazon](https://www.amazon.com/gp/product/B0CHQ97KQZ/)
* \$13.29 for 5 pieces = $2.66/piece, though had free deliverey.
* Digikey has for \$1.66/piece in quantity 1, $1.52 in quantity 25.

## Servo Motor

[Amazon](https://www.amazon.com/gp/product/B092VN3MTX/)

## Poteniometer

[Amazon](https://www.amazon.com/gp/product/B09897HR3C/)



  You may need to install the following packages for this specific kernel:
    linux-tools-5.15.90.1-microsoft-standard-WSL2
    linux-cloud-tools-5.15.90.1-microsoft-standard-WSL2

  You may also want to install one of the following packages to keep up to date:
    linux-tools-standard-WSL2
    linux-cloud-tools-standard-WSL2
