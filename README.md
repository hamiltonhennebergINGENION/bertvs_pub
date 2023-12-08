# ber-tvs

A bit error rate test for the Total Verification System. Contains the software interface to the BER TVS.

## Installing ber-tvs

Installing the ber-tvs program is very simple. The TVS  uses Opal Kelly's Front Pannel API and can only communicate with the program if the Front Pannel USB driver is installed. Just pick the latest one from the link bellow and install:

https://pins.opalkelly.com/downloads

Outside of that the ber-tvs example code utilizes only python with the pandas and numpy libraries installed. Pandas is dependent on numpy so this should be the only python install package needed to run the program:
`pip install pandas`

## Starting the program

To start the TVS Testing program there are two ways:

- The easiest way is to execute the `bertvs_gui.py` file from the `BER-TVS` folder in VS Code.
- Alternatively use the command line, cd to the repository folder, and run `python3 py/bertvs_gui.py`

## TVS Testing Information

Start by entering your name into the Inspector box.
- Enter a serial number before hitting start
- Notes are not required but can be helpful

After starting the test the 2nd window should activate.
- Each port is given a percent change indicator, when this hits 100% the test is complete.
- If an LED does not light up or complete, refer to log file to see which pin is malfunctioning.
- For each successful loopback the color should progress:

  1. Orange
  2. Yellow
  3. Green

## Additional 

To use a venv with BER here is a shell script for that case, make sure to set the correct path directories!
```
#!/bin/sh
export FP_ROOT='/opt/FrontPanel-Ubuntu20.04LTS-x64-5.2.7/' # make sure this is your path
export PYTHONPATH=$FP_ROOT/API/Python3:$PYTHONPATH
export LD_LIBRARY_PATH=$FP_ROOT/API/Python3:$FP_ROOT/API:$LD_LIBRARY_PATH
source py/.venv/bin/activate
python3 py/bertvs_gui.py
deactivate
```
