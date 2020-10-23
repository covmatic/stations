
from opentrons.types import Point
from system9.b import magnets
import json
import os
import math
from typing import Optional

from opentrons.protocol_api import ProtocolContext
from threading import Thread
import time

metadata = {
    'protocolName': 'Version 1 S9 Station B Technogenetics (630µl sample input)',
    'author': 'Marco & Giada',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 30  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
NUM_SEDUTE = 1
ELUTION_VOL = 40
TIP_TRACK = False
PARK = False

SKIP_DELAY = False

ELUTE_ASPIRATION_RATE = 50


MAG_OFFSET = -0.35

class BlinkingLight(Thread):
    def __init__(self, ctx: ProtocolContext, t: float = 1):
        super(BlinkingLight, self).__init__()
        self._on = False
        self._state = True
        self._ctx = ctx
        self._t = t
    
    def stop(self):
        self._on = False
        self.join()

    def switch(self, x: Optional[bool] = None):
        self._state = not self._state if x is None else x
        self._ctx._hw_manager.hardware.set_lights(rails=self._state)
            
    def run(self):
        self._on = True
        state = self._ctx._hw_manager.hardware.get_lights()
        while self._on:
            self.switch()
            time.sleep(self._t)
        self.switch(state)

def delay(minutesToDelay, message, context):
    message += ' for ' + str(minutesToDelay) + ' minutes.'
    if SKIP_DELAY:
        context.pause(message  + "Pausing for skipping delay. Please resume")
    else:
        context.delay(minutes=minutesToDelay, msg=message)


def run(ctx):
    ctx.comment("Protocollo Techonogenetics Stazione B - Rimozione Eluato per {} campioni".format(NUM_SAMPLES))
    ctx.comment("Mettere la deepwell nel modulo magnetico")
    
    # --- Definitions ---------------------------------------------------------
    # Tips and pipettes
    num_cols = math.ceil(NUM_SAMPLES/8)
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200µl filtertiprack')
        for slot in ['2', '3', '5', '6', '7', '8', '9']
    ]
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)
    
    # Magnetic module
    magdeck = ctx.load_module('Magnetic Module Gen2', '4')
    magdeck.disengage()
    magheight = MAG_OFFSET + magnets.height.by_serial.get(magdeck._module._driver.get_device_info()['serial'], 6.65)
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    
    # PCR plate
    pcr_plate = ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block for Station C')
    
    # Positions
    mag_samples_m = magplate.rows()[0][:num_cols]
    pcr_samples_m = pcr_plate.rows()[0][:num_cols]
    # -------------------------------------------------------------------------
    
    # --- Functions -----------------------------------------------------------
    folder_path = '/data/B'
    tip_file_path = folder_path + '/tip_log.json'
    tip_log = {'count': {}}
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips300' in data:
                    tip_log['count'][m300] = data['tips300']
                else:
                    tip_log['count'][m300] = 0
        else:
            tip_log['count'][m300] = 0
    else:
        tip_log['count'] = {m300: 0}

    tip_log['tips'] = {
        m300: [tip for rack in tips300 for tip in rack.rows()[0]]}
    tip_log['max'] = {m300: len(tip_log['tips'][m300])}

    def pick_up(pip, loc=None):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip] and not loc:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        if loc:
            pip.pick_up_tip(loc)
        else:
            pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
            tip_log['count'][pip] += 1

    switch = True
    drop_count = 0
    drop_threshold = 296  # number of tips trash will accommodate before prompting user to empty

    def drop(pip):
        nonlocal switch
        nonlocal drop_count
        side = 30 if switch else -18
        drop_loc = ctx.loaded_labwares[12].wells()[0].top().move(
            Point(x=side))
        pip.drop_tip(drop_loc)
        switch = not switch
        drop_count += 8
        if drop_count == drop_threshold:
            # Setup for flashing lights notification to empty trash
            ctx.pause('Please empty tips from waste before resuming.')
            ctx.home()  # home before continuing with protocol
            drop_count = 0
    # -------------------------------------------------------------------------
    
    # --- RUN -----------------------------------------------------------------
    for i in range(NUM_SEDUTE):
        ctx.comment("Seduta {}/{}".format(i + 1, NUM_SEDUTE))
        magdeck.engage(height=magheight)
        delay(2, 'Incubazione a RT con modulo magnetico attivo', ctx)
        for i, (m, e) in enumerate(zip(mag_samples_m, pcr_samples_m)):
            pick_up(m300)
            m300.flow_rate.aspirate = ELUTE_ASPIRATION_RATE
            m300.transfer(ELUTION_VOL, m.bottom(0.1), e.bottom(5), air_gap=20, new_tip='never')
            drop(m300)
        
        magdeck.disengage()
    
        if NUM_SEDUTE > 1:
            blight = BlinkingLight(ctx=ctx)
            blight.start()
            ctx.home()
            ctx.pause("Rimuovere le piastre, conservare la NEST plate a +4°C e la deepwell sul modulo di temperatura della Stazione B. \nCaricare le nuove piastre se necessario. \nPremere Resume.")
            blight.stop()
    # -------------------------------------------------------------------------
