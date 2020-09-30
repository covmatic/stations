from opentrons import protocol_api
import json
import os
import math
from typing import Optional

from opentrons.protocol_api import ProtocolContext
from threading import Thread
import time

# metadata
metadata = {
    'protocolName': 'Version 1 Station A Technogenetics',
    'author': 'Marco & Giada',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 16
SAMPLE_VOLUME = 200
LYSIS_VOLUME = 400
PK_VOLUME = 30
BEADS_VOLUME = 10
TIP_TRACK = False

DEFAULT_ASPIRATE = 100
DEFAULT_DISPENSE = 100

LYSIS_RATE_ASPIRATE = 100
LYSIS_RATE_DISPENSE = 100

liquid_headroom = 1.1
pk_capacity = 180

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

def run(ctx: protocol_api.ProtocolContext):
    ctx.comment("Protocollo Technogenetics Stazione A per {} COPAN 330C tamponi.".format(NUM_SAMPLES))
    # load labware
    source_racks = [ctx.load_labware('copan_24_tuberack_14000ul', slot,
			'source tuberack ' + str(i+1))
        for i, slot in enumerate(['2', '3', '5', '6'])
    ]
    dest_plate = ctx.load_labware(
        'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate')
    tempdeck = ctx.load_module('Temperature Module Gen2', '10')
    
    strips_block = tempdeck.load_labware(
       'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
       'chilled tubeblock for proteinase K (first 3 strips) and beads (strip 12)')
    beads = strips_block.rows()[0][11]
    
    lys_buff = ctx.load_labware(
        'opentrons_6_tuberack_falcon_50ml_conical', '4',
        '50ml tuberack for lysis buffer + PK (tube A1)').wells()[0]
    tipracks1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot,
                                     '1000µl filter tiprack')
                    for slot in ['8', '9']]
    tipracks20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot,
                                   '20µl filter tiprack')
                    for slot in['7', '11']]

    # load pipette
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tipracks20)
    p1000 = ctx.load_instrument(
        'p1000_single_gen2', 'right', tip_racks=tipracks1000)
    p1000.flow_rate.aspirate = DEFAULT_ASPIRATE
    p1000.flow_rate.dispense = DEFAULT_DISPENSE
    p1000.flow_rate.blow_out = 300
 
    # setup samples
    # we try to allocate the maximum number of samples available in racks (e.g. 15*number of racks)
    # and after we will ask the user to replace the samples to reach NUM_SAMPLES
    # if number of samples is bigger than samples in racks.
    sources = [
        well for rack in source_racks for well in rack.wells()][:NUM_SAMPLES]
    max_sample_per_set = len(sources)
    set_of_samples = math.ceil(NUM_SAMPLES/max_sample_per_set)
   
    # setup proteinase K
    num_cols = math.ceil(NUM_SAMPLES/8)
    num_pk_strips = math.ceil( PK_VOLUME * num_cols * liquid_headroom / pk_capacity)
    pk_cols_per_strip = math.ceil(num_cols/num_pk_strips)
    
    prot_K_strips = strips_block.rows()[0][:num_pk_strips]
    ctx.comment("Proteinase K: usare {} strips con almeno {:.2f} uL ogni pozzetto".format(num_pk_strips, pk_cols_per_strip * PK_VOLUME * liquid_headroom))

    # setup destinations
    dests_single = dest_plate.wells()[:NUM_SAMPLES]
    dests_multi = dest_plate.rows()[0][:math.ceil(NUM_SAMPLES/8)]

    tip_log = {'count': {}}
    folder_path = '/data/A'
    tip_file_path = folder_path + '/tip_log.json'
    if TIP_TRACK and not ctx.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                if 'tips1000' in data:
                    tip_log['count'][p1000] = data['tips1000']
                else:
                    tip_log['count'][p1000] = 0
                if 'tips20' in data:
                    tip_log['count'][m20] = data['tips20']
                else:
                    tip_log['count'][m20] = 0
    else:
        tip_log['count'] = {p1000: 0, m20: 0}

    tip_log['tips'] = {
        p1000: [tip for rack in tipracks1000 for tip in rack.wells()],
        m20: [tip for rack in tipracks20 for tip in rack.rows()[0]]
    }
    tip_log['max'] = {
        pip: len(tip_log['tips'][pip])
        for pip in [p1000, m20]
    }

    def pick_up(pip):
        nonlocal tip_log
        if tip_log['count'][pip] == tip_log['max'][pip]:
            ctx.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
            pip.reset_tipracks()
            tip_log['count'][pip] = 0
        pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
        tip_log['count'][pip] += 1

    lysis_total_vol = LYSIS_VOLUME * NUM_SAMPLES * liquid_headroom
    beads_total_vol = BEADS_VOLUME * NUM_SAMPLES * liquid_headroom

    ctx.comment("Volume Lysis Buffer: {} mL".format(lysis_total_vol/1000))
    ctx.comment("Volume Beads: {} ul per pozzetto della strip".format(beads_total_vol/8))
    
    radius = (lys_buff.diameter)/2
    heights = {lys_buff: lysis_total_vol/(math.pi*(radius**2))}
    ctx.comment("Lysis buffer expected initial height: {:.2f} mm".format(heights[lys_buff]))
    min_h = 5

    def h_track(tube, vol, context):
        nonlocal heights
        dh = vol/(math.pi*(radius**2))
        if heights[tube] - dh > min_h:
            heights[tube] = heights[tube] - dh
        else:
            heights[tube] = min_h
        context.comment("Going {} mm deep".format(heights[tube]))
        return tube.bottom(heights[tube])
        
    
    # transfer proteinase K
    pick_up(m20)
    for idx, d in enumerate(dests_multi):
        strip_ind = idx // pk_cols_per_strip
        prot_K = prot_K_strips[strip_ind]
        m20.transfer(PK_VOLUME, prot_K, d.bottom(2), new_tip='never')
    m20.drop_tip()
    
    # transfer sample
    done_samples = 0
    refill_of_samples = set_of_samples - 1  # the first set is already filled before start
    ctx.comment("Using {} samples per time".format(max_sample_per_set))
    ctx.comment("We need {} samples refill.".format(refill_of_samples))
    
    for i in range(set_of_samples):
        # setup samples
        remaining_samples = NUM_SAMPLES - done_samples
        ctx.comment("Remaining {} samples".format(remaining_samples))
        
        set_of_sources = sources[:remaining_samples]    # just eventually pick the remaining samples if less than full rack
        destinations = dests_single[done_samples:(done_samples + len(sources))]
  
        ctx.comment("Transferring {} samples".format(len(sources)))
        
        for s, d in zip(sources, destinations):
            pick_up(p1000)
            p1000.mix(1, 150, s.bottom(6))
            p1000.transfer(SAMPLE_VOLUME, s.bottom(3), d.bottom(5), air_gap=100, new_tip='never')
            p1000.air_gap(100)
            p1000.drop_tip()

        done_samples = done_samples + len(sources)
        ctx.comment("Done {} samples".format(done_samples))

        if i < (refill_of_samples):
            ctx.pause("Please refill samples")
    
    
    # transfer lysis buffer
    p1000.flow_rate.aspirate = LYSIS_RATE_ASPIRATE
    p1000.flow_rate.dispense = LYSIS_RATE_DISPENSE
    for s, d in zip(sources, dests_single):
        pick_up(p1000)
        p1000.transfer(LYSIS_VOLUME, h_track(lys_buff, LYSIS_VOLUME, ctx), d.bottom(5), air_gap=100,
                       mix_after=(2, 100), new_tip='never')
        p1000.air_gap(100)
        p1000.drop_tip()
    
    blight = BlinkingLight(ctx=ctx)
    blight.start()
    ctx.delay(30)
    ctx.pause("Sigillare la deepwell con un adesivo. \nMettere la deepwell nel thermomixer: 700 rpm RT per 3 min. \nAl termine spostare la deepwell nell'incubatore per 20 minuti a 55°C.")
    blight.stop()
    
    # transfer beads
    for idx, d in enumerate(dests_multi):
        pick_up(m20)
        # transferring beads
        # no air gap to use 1 transfer only avoiding drop during multiple transfers.
        m20.transfer(BEADS_VOLUME, beads, d.bottom(2), air_gap = 5,
                     new_tip='never')
        m20.mix(2, 20, d.bottom(2))
        m20.air_gap(5)
        m20.drop_tip()

    ctx.comment('Sposta la deepwell nella Stazione B per procedere con l\'estrazione.')

    # track final used tip
    if not ctx.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {
            'tips1000': tip_log['count'][p1000],
            'tips20': tip_log['count'][m20]
        }
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)



# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
