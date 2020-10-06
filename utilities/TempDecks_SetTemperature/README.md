# TempDeck Control script

## Introduction
This small piece of python script helps to control the **Opentrons Temperature Module** (here referred as *TempDeck*).
You can find more information about it [here](https://support.opentrons.com/en/articles/1820119-temperature-module)

## Installation
The script uses **pyserial** and **opentrons** packages.
Install them with the command:
```
py -m pip install -r requirements.txt --upgrade
```

## Usage
Using the script should be easy:
1. clone or download the directory;
1. open *TempDecks_SetTemperature.bat*: the program shows the TempDecks found;
1. write the desidered temperature and press *Enter*;
1. when finished press a key and the program will **deactivates** all the modules and exit.


<!---
Copyright (c) 2020 Covmatic.
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->