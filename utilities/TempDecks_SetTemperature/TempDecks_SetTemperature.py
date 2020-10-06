# Python script to interact with the
# Opentrons Temperature module.
#
# It search for TempDeck module connected with USB
# and set for each of them the temperature give as 
# input.
# Than the program wait for a keypress before deactivating the 
# module and exit.

import serial
import sys
from opentrons.drivers import temp_deck
from serial.tools.list_ports import comports

PID_TEMPDECK = 61075
DEFAULT_TEMPERATURE = 55

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("\t=============================")
    print("\t  TempDeck Set Temperature   ")
    print("\t=============================")
    print("\nProgramma per settare la temperatura\n \
dei moduli temperatura Opentrons.")
    print("\n\nCerco le porte seriali...")
    ports = []
    for p in comports():
        print("Trovata {}".format(p.device))
        if(p.pid == PID_TEMPDECK):
            print("\t\tTempDeck!")
            ports.append(p.device)
    #TempMomdule = TempModuleDriver("COM5")

    print("Trovati {} tempdeck".format(len(ports)))

    if(len(ports) == 0):
        print("Non ho trovato nessun tempdeck.")
        exit(1)

    rawtemp = input("\nInserisci la temperatura da settare: ({}): ".format(DEFAULT_TEMPERATURE))
    try:
        temperature = int(rawtemp)
    except:
        print("\nErrore nel riconoscere la temperatura. Uso il default")
        temperature = DEFAULT_TEMPERATURE

    tempdecks = []
    for p in ports:
        td = temp_deck.TempDeck()
        tempdecks.append(td)

    for p, td in zip(ports, tempdecks):
        td.connect(p)
        print("Apro {}".format(td.port))
        if(td.is_connected()):
            print("\t\ttempdeck connesso!")
            print("Setto {} a {}°C".format((td.port), temperature))
            td.start_set_temperature(temperature)
        else:
            print("Errore nella connessione al tempdeck su {}!".format(td.port))


    print("Premere un tasto per disattivare ed uscire...")
    sys.stdin.read(1)

    for td in tempdecks:
        if(td.is_connected()):
            td.deactivate()
            td.disconnect()

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.