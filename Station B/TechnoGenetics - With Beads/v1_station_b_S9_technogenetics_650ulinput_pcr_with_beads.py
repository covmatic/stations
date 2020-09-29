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

NUM_SAMPLES = 11  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
STARTING_VOL = 650
ELUTION_VOL = 50
WASH_VOL = 680
TIP_TRACK = False
PARK = False

SKIP_DELAY = False

DEFAULT_ASPIRATION_RATE	= 150
SUPERNATANT_REMOVAL_ASPIRATION_RATE = 25
ELUTE_ASPIRATION_RATE = 50
LAST_RATE_ASPIRATE = 30
LAST_RATE_DISPENSE = 30

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
    ctx.comment("Protocollo Techonogenetics Stazione B per {} campioni".format(NUM_SAMPLES))
    ctx.comment("Mettere la deepwell nel modulo magnetico")
    
    # --- Definitions ---------------------------------------------------------
    # Tips and pipettes
    num_cols = math.ceil(NUM_SAMPLES/8)
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200µl filtertiprack')
        for slot in ['3', '6', '8', '9', '10']
    ]
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)
    
    # Temperature module
    tempdeck = ctx.load_module('Temperature Module Gen2', '7')
    tempplate = tempdeck.load_labware('nest_96_wellplate_2ml_deep')
    
    # Magnetic module
    magdeck = ctx.load_module('Magnetic Module Gen2', '4')
    magdeck.disengage()
    magheight = MAG_OFFSET + magnets.height.by_serial.get(magdeck._module._driver.get_device_info()['serial'], 6.65)
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    
    # PCR plate
    pcr_plate = ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block for Station C')
    
    # Liquids
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11', 'Liquid Waste').wells()[0].top()
    res12 = ctx.load_labware('nest_12_reservoir_15ml', '5', 'Trough with WashReagents')
    elut12 = ctx.load_labware('nest_12_reservoir_15ml', '2', 'Trough with Elution')
    washA = res12.wells()[:6]
    washB = res12.wells()[-6:]
    elution = elut12.wells()[-1]
    
    # Positions
    mag_samples_m = magplate.rows()[0][:num_cols]
    pcr_samples_m = pcr_plate.rows()[0][:num_cols]
    temp_samples_m = tempplate.rows()[0][:num_cols]
    # -------------------------------------------------------------------------
    
    # --- Setup ---------------------------------------------------------------
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300
    tempdeck.set_temperature(55)
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
    
    def mix(repetition, vol, slot):
        for i, m in enumerate(slot):
            pick_up(m300)
            m300.mix(repetition, vol, m.bottom(0.3))
            m300.air_gap(20)
            drop(m300)
        
    def remove_supernatant(vol):
        m300.flow_rate.aspirate = SUPERNATANT_REMOVAL_ASPIRATION_RATE
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, m in enumerate(mag_samples_m):
            pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.5).move(Point(x=side*2))
            for _ in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, m.top())  # void air gap if necessary
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, loc, waste, new_tip='never',
                              air_gap=20)
                m300.air_gap(20)
            drop(m300)
        m300.flow_rate.aspirate = DEFAULT_ASPIRATION_RATE
        
    def remove_wash(vol):
        m300.flow_rate.aspirate = SUPERNATANT_REMOVAL_ASPIRATION_RATE
        num_trans = math.ceil(vol/200)
        vol_per_trans = vol/num_trans
        for i, m in enumerate(mag_samples_m):
            pick_up(m300)
            for _ in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, m.top())  # void air gap if necessary
                m300.move_to(m.center())
                m300.transfer(vol_per_trans, m.bottom(0.2), waste, new_tip='never',
                              air_gap=20)
                m300.air_gap(20)
            drop(m300)
        m300.flow_rate.aspirate = DEFAULT_ASPIRATION_RATE

    def wash(wash_vol, source, mix_reps):
        magdeck.disengage()

        num_trans = math.ceil(wash_vol/200)
        vol_per_trans = wash_vol/num_trans
        for i, m in enumerate(mag_samples_m):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            src = source[i//(12//len(source))]
            for n in range(num_trans):
                if m300.current_volume > 0:
                    m300.dispense(m300.current_volume, src.top())
                m300.transfer(vol_per_trans, src, m.top(), air_gap=20,
                              new_tip='never')
                if n < num_trans - 1:  # only air_gap if going back to source
                    m300.air_gap(20)
            m300.mix(mix_reps, 150, loc)
            drop(m300)

        magdeck.engage(height=magheight)
        delay(5, 'Incubating on MagDeck', ctx)
        remove_supernatant(wash_vol)
        
    wash_tot_vol = NUM_SAMPLES * WASH_VOL *1.1
    ctx.comment("Volume Wash A: {} mL".format(wash_tot_vol/1000))
    ctx.comment("Volume Wash B: {} mL".format(wash_tot_vol/1000))
    
    def elute(vol):
        magdeck.disengage()
        
        # resuspend beads in elution
        m300.flow_rate.aspirate = ELUTE_ASPIRATION_RATE
        for i, m in enumerate(temp_samples_m):
            pick_up(m300)
            m300.aspirate(vol, elution)
            m300.move_to(m.center())
            m300.dispense(vol, m.bottom(0.7))
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.3).move(Point(x=side*2))
            m300.mix(15, 30, loc)
            m300.touch_tip(v_offset=-5)
            m300.air_gap(20)
            drop(m300)
            
    elution_tot_vol = NUM_SAMPLES * ELUTION_VOL * 1.1
    ctx.comment("Volume Elution Solution: {} mL".format(elution_tot_vol/1000))
    # -------------------------------------------------------------------------
    
    # --- RUN -----------------------------------------------------------------
    mix(10, 180, mag_samples_m)
    delay(20, 'Incubazione delle biglie a RT', ctx)
    magdeck.engage(height=magheight)
    delay(5, 'Incubazione a RT con modulo magnetico attivo', ctx)
    
    remove_supernatant(STARTING_VOL)
    wash(WASH_VOL, washA, 20)
    wash(WASH_VOL, washB, 20)
    
    blight = BlinkingLight(ctx=ctx)
    blight.start()
    ctx.delay(30)
    ctx.pause("Spinnare la deepwell per 20 sec a RT.\nAl termine rimettere la deepwell nel modulo magnetico.")
    blight.stop()
    
    magdeck.engage(height=magheight)
    delay(3, 'Incubazione a RT con modulo magnetico attivo', ctx)
    remove_wash(50)
    magdeck.disengage()
    
    blight = BlinkingLight(ctx=ctx)
    blight.start()
    ctx.delay(30)
    ctx.pause("Spostare la deepwell sul modulo di temperatura a 55°C senza premere Resume. \nIncubare per almeno 40 min, impostare timer. \nAd asciugatura completa, premere Resume. \nN.B. PREPARARE LA PCR PLATE NELLA STAZIONE C.")
    blight.stop()
    
    elute(ELUTION_VOL)
    
    blight = BlinkingLight(ctx=ctx)
    blight.start()
    ctx.delay(30)
    ctx.pause("Sigillare la deepwell con un adesivo. \nMettere la deepwell nel thermomixer: 700 rpm 55°C per almeno 5 min. \nA biglie risospese, posizionare la deepwell sul modulo MAGNETICO e cliccare Resume.")
    blight.stop()
    
    magdeck.engage(height=magheight)
    delay(5, 'Incubazione a RT con modulo magnetico attivo', ctx)
    
    blight = BlinkingLight(ctx=ctx)
    blight.start()
    ctx.delay(30)
    ctx.pause("Mettere la PCR plate nello slot 1, sulla piastra di alluminio.")
    blight.stop()

    m300.flow_rate.aspirate = LAST_RATE_ASPIRATE
    m300.flow_rate.dispense = LAST_RATE_DISPENSE
    for i, (m, e) in enumerate(zip(mag_samples_m, pcr_samples_m)):
            pick_up(m300)
            side = -1 if i % 2 == 0 else 1
            loc = m.bottom(0.3).move(Point(x=side*2))
            m300.transfer(20, loc, e.bottom(5), air_gap=20, new_tip='never')
            m300.mix(5, 20, e.bottom(1.5))
            m300.air_gap(20)
            drop(m300)
    
    magdeck.disengage()
    ctx.comment("Spostare la PCR plate nella RT-PCR.")
    # -------------------------------------------------------------------------


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
