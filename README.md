# MTA Portal

<!-- <img src="MTAPortal.jpg" alt="drawing" width="300"/> -->

Run your own MTA Portal on CircuitPython to display trains arrivals using Adafruit's [hardware](https://www.adafruit.com/product/4812) and libraries.

Follow Adafruit main [tutorial](https://learn.adafruit.com/adafruit-matrixportal-m4) to set up your MatrixPortal. Basically,

1. Connect your terminals into the display
2. Connect your circuit into the display
3. Connect to your computer via *data* USB C cable
4. Click the reset button on the circuit twice, which will trigger a bootloader mode and mount a device
5. Copy over the uf2 file you got from the tutorial
6. Copy over all of the contents of this repo to the drive 
7. In a separate terminal run `python3 serial_monitor.py` to watch the debug output
8. Any writes to disk will trigger a restart of `code.py`, and be displayed in the terminal above. There's a vscode/cursor project setting in this repo that will automatically cp over the file to trigger the write + restart from your main disk. I would not recommend opening the project on the mounted disk for obvious reasons.
9. This is just to get `code.py` running, follow the below steps to get the business logic functional.

## Config
You'll also need to 

1. Sign up for [io.adafruit.com](io.adafruit.com) so that you can get the clock time using their API
2. [Upgrade your esp32 firmware to 3.x so that HTTPS calls to the train API works](https://learn.adafruit.com/upgrading-esp32-firmware/upgrade-all-in-one-esp32-airlift-firmware)
3. Set up your `settings.toml` by renaming `example_settings.toml` to the former and adding your wifi info and adafruit account info.
4. Edit `code.py` so that you get your [relevant stop info](https://github.com/jonthornton/MTAPI/blob/master/data/stations.json) and directions, etc. Would advise just to use an LLM for this.

