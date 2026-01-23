# MTA Portal

<img src="https://github.com/user-attachments/assets/c5b749e5-761c-424d-8fc3-86d4a623432e" alt="drawing" width="500"/>

Run your own MTA Portal on CircuitPython to display trains arrivals using Adafruit's [hardware](https://www.adafruit.com/product/4812) and libraries.

Follow Adafruit main [tutorial](https://learn.adafruit.com/adafruit-matrixportal-m4) to set up your MatrixPortal. 

## Setup to get code running on your device but not yet business-functional
There's a few incantations and dances you'll have to do to set up everything, maybe 10 minutes. 

TODO: A script to automate all this?

1. Connect your terminals into the display (red and black cables)
2. Connect your circuit into the display  (The module into the display board)
3. Connect to your computer via *data* USB C cable 
4. Click the reset button on the circuit twice, which will trigger a bootloader mode and mount a device. 
5. Copy over the uf2 file you got from the tutorial, should be for CircuitPython 10.x
6. Copy over all of the contents of this repo to the drive 
7. In a separate terminal run `uv run serial_monitor.py` to watch the debug output
8. Any writes to disk will trigger a restart of `code.py`, and be displayed in the terminal above. There's a vscode/cursor project setting in this repo that will automatically cp over the file to trigger the write + restart from your main disk. I would not recommend opening the project on the mounted disk for obvious reasons.
9. This is just to get `code.py` running, follow the below steps to get the business logic functional.

## Config
You'll also need to

1. [Upgrade your esp32 firmware to 3.x so that HTTPS calls to the train API works](https://learn.adafruit.com/upgrading-esp32-firmware/upgrade-all-in-one-esp32-airlift-firmware). Remember to repeat steps 4 and 5 from above after using NINA to upgrade the firmware.
2. Set up your `settings.toml` by renaming `example_settings.toml` to the former and adding your wifi info.
3. Edit `code.py` so that you get your [relevant stop info](https://github.com/jonthornton/MTAPI/blob/master/data/stations.json) and directions, etc. Would advise just to use an LLM for this.
4. Save the file which will trigger a cp to the mounted device and trigger a restart.

Forked from https://github.com/thejsj/mta-portal, which apparently itself is a fork. Shoutout Jorge . This one's more noob friendly and I save you all the meandering I had to endure as a software engineer who doesn't know anything about hardware. If you follow the steps exactly as I listed, you will get a working demo. If you know what you're doing then use Jorge's repo because it's way more minimal.
