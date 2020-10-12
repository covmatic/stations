from opentrons import protocol_api
import json
import os
import math
from typing import Optional
from itertools import repeat, chain

from opentrons.protocol_api import ProtocolContext
from threading import Thread
import time


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


# metadata
metadata = {
    'protocolName': 'Version 1 S9 Station C Technogenetics P20 Multi',
    'author': 'Nick Pootza<protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


NUM_SAMPLES = 16  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
NUM_SEDUTE = 2
TIP_TRACK = False

liquid_headroom = 1.1
mm_tube_capacity = 1950
mm_strips_capacity = 180

mm_mix = {
    "a": 6,
    "b": 8,
    "c": 6,
}
MM_PER_SAMPLE = sum(mm_mix.values())


def run(ctx: protocol_api.ProtocolContext):
    global MM_TYPE

    ctx.comment("Protocollo Technogenetics Stazione C per {} campioni.".format(NUM_SAMPLES))

    # check source (elution) labware type
    source_plate = ctx.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul', '1',
        'chilled elution plate on block for Station B')
    tips20 = [
        ctx.load_labware('opentrons_96_filtertiprack_20ul', slot)
        for slot in ['2', '3', '6', '7', '9', '11']
    ]
    
    tips300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', '10')]
    tempdeck = ctx.load_module('Temperature Module Gen2', '4')
    pcr_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_biorad_wellplate_200ul', 'PCR plate')
    mm_strips = ctx.load_labware(
        'opentrons_96_aluminumblock_generic_pcr_strip_200ul', '8',
        'mastermix strips')
    #tempdeck.set_temperature(4)
    tube_block = ctx.load_labware(
        'opentrons_24_aluminumblock_nest_2ml_screwcap', '5',
        '2ml screw tube aluminum block for mastermix + controls')
    
    # pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'right', tip_racks=tips20)
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips300)

    # setup up sample sources and destinations
    num_cols = math.ceil(NUM_SAMPLES/8)
    sources = source_plate.rows()[0][:num_cols]
    sample_dests = pcr_plate.rows()[0][:num_cols]

    tip_log = {'count': {}}
    folder_path = '/data/C'
    tip_file_path = folder_path + '/tip_log.json'
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips20' in data:
                    tip_log['count'][m20] = data['tips20']
                else:
                    tip_log['count'][m20] = 0
                if 'tips300' in data:
                    tip_log['count'][p300] = data['tips300']
                else:
                    tip_log['count'][p300] = 0
        else:
            tip_log['count'] = {m20: 0, p300: 0}
    else:
        tip_log['count'] = {m20: 0, p300: 0}

    tip_log['tips'] = {
        m20: [tip for rack in tips20 for tip in rack.rows()[0]],
        p300: [tip for rack in tips300 for tip in rack.wells()]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [m20, p300]
    }

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            # print('Replace ' + str(pip.max_volume) + 'µl tipracks before resuming.')
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1
        # print("Picked up {} with {} [#{}]".format(tip_log['tips'][pip][tip_log['count'][pip]-1], pip, tip_log['count'][pip]))

    """ mastermix component maps """
    # setup tube mastermix
    num_mm_tubes = math.ceil( MM_PER_SAMPLE * NUM_SAMPLES * liquid_headroom / mm_tube_capacity)
    samples_per_mm_tube = []
    for i in range(num_mm_tubes):
        remaining_samples = NUM_SAMPLES - sum(samples_per_mm_tube)
        samples_per_mm_tube.append(min(8 * math.ceil(remaining_samples / (8 * (num_mm_tubes - i))), remaining_samples))
    mm_per_tube = [MM_PER_SAMPLE * liquid_headroom * ns for ns in samples_per_mm_tube]
    
    mm_tube = tube_block.wells()[:num_mm_tubes]
    # ctx.comment("Mastermix: caricare {} tubes con almeno [{}] uL ciascuno".format(num_mm_tubes, ", ".join(map(str, map(round, mm_per_tube)))))
    ndigs = math.ceil(math.log10(math.floor(max(mm_per_tube) + 1)))
    fmt = lambda n: ("{:>" + str(ndigs + 3) + "}").format("{:.2f}".format(n)) 
    msg = "Mastermix: caricare {} tube{} con almeno".format(num_mm_tubes, "" if num_mm_tubes == 1 else "s")
    for i, (mt, mm, ns) in enumerate(zip(mm_tube, mm_per_tube, samples_per_mm_tube)):
        msg += (
            "\n  {} --> {} uL".format(str(mt).split(" ")[0], fmt(mm)) +
            "".join("\n    {} -> {} uL".format(k, fmt(ns * v * liquid_headroom)) for k, v in mm_mix.items())
        )
    for r in msg.split("\n"):
        while "  " in r: r = r.replace("  ", "\u2007 ")
        ctx.comment(r)
    
    #setup strips mastermix
    mm_strip = mm_strips.columns()[:num_mm_tubes]
    
    mm_indices = list(chain.from_iterable(repeat(i, ns) for i, ns in enumerate(samples_per_mm_tube)))

    # for _ in range(5):
    #    test_light = BlinkingLight(ctx)
    #    test_light.start()
    #    ctx.delay(30)
    #    test_light.stop()
    
    #### START REPEATED SECTION
    for i in range(NUM_SEDUTE):
        ctx.comment("Seduta {}/{}".format(i + 1, NUM_SEDUTE))
        # transfer mastermix to strips
        pick_up(p300)
        for mt, ms, ns in zip(mm_tube, mm_strip, samples_per_mm_tube):
            for strip_i, strip_w in enumerate(ms):
                p300.transfer((ns // 8 + (1 if strip_i < ns % 8 else 0)) * MM_PER_SAMPLE * liquid_headroom, mt.bottom(0.2), strip_w, new_tip='never')
        p300.drop_tip()
    
        # transfer mastermix to plate
        pick_up(m20)
        for m_idx, s in zip(mm_indices[::8], sample_dests):
            m20.transfer(18, mm_strip[m_idx][0].bottom(0.5), s, new_tip='never')
        m20.drop_tip()
        ctx.pause("Sigillare la PCR plate con un adesivo. \nRiporre la PCR plate a +4°C.")
        
        if i < NUM_SEDUTE - 1:
            blight = BlinkingLight(ctx=ctx)
            blight.start()
            ctx.home()
            # print("Please, load a new plate from station B. Resume when it is ready")
            ctx.pause("Please, load a new plate from station B. Also, refill mastermix. Resume when it is ready")
            blight.stop()
    #### END REPEATED SECTION
    
    # track final used tip
    if TIP_TRACK and not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips20': tip_log['count'][m20],
            'tips300': tip_log['count'][p300]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)


if __name__ == "__main__":
    from opentrons import simulate  
    run(simulate.get_protocol_api(metadata["apiLevel"]))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
