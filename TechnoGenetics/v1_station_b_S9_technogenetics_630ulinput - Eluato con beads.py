from opentrons.types import Point
from system9.b import magnets
import json
import os
import math

metadata = {
    'protocolName': 'Version 1 S9 Station B Technogenetics (630µl sample input)',
    'author': 'Marco & Giada',
    'apiLevel': '2.3'
}

NUM_SAMPLES = 8  # start with 8 samples, slowly increase to 48, then 94 (max is 94)
STARTING_VOL = 650
ELUTION_VOL = 40
TIP_TRACK = False
PARK = False

SKIP_DELAY = False

DEFAULT_ASPIRATION_RATE	= 150
SUPERNATANT_REMOVAL_ASPIRATION_RATE = 25
ELUTE_ASPIRATION_RATE = 50

MAG_OFFSET = -0.35


def delay(minutesToDelay, message, context):
    message += ' for ' + str(minutesToDelay) + ' minutes.'
    if SKIP_DELAY:
        context.pause(message  + "Pausing for skipping delay. Please resume")
    else:
        context.delay(minutes=minutesToDelay, msg=message)


def run(ctx):
    ctx.comment("Station B Technogenetics protocol for {} samples".format(NUM_SAMPLES))
    
    # --- Definitions ---------------------------------------------------------
    # Tips and pipettes
    num_cols = math.ceil(NUM_SAMPLES/8)
    tips300 = [
        ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200µl filtertiprack')
        for slot in [ '3', '7', '8', '9', '10']
    ]
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)
    
    # Magnetic module
    magdeck = ctx.load_module('Magnetic Module Gen2', '4')
    magdeck.disengage()
    magheight = MAG_OFFSET + magnets.height.by_serial.get(magdeck._module._driver.get_device_info()['serial'], 6.65)
    magplate = magdeck.load_labware('nest_96_wellplate_2ml_deep')
    
    # Temperature module
    # tempdeck = ctx.load_module('Temperature Module Gen2', '6')
    # tempplate = tempdeck.load_labware('nest_96_wellplate_2ml_deep')
    
    # PCR plate
    pcr_plate = ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', '1', 'chilled elution plate on block for Station C')
    
    # Liquids
    waste = ctx.load_labware('nest_1_reservoir_195ml', '11', 'Liquid Waste').wells()[0].top()
    res12 = ctx.load_labware('nest_12_reservoir_15ml', '5', 'Trough with WashReagents')
    elut12 = ctx.load_labware('nest_12_reservoir_15ml', '2', 'Trough with Elution')
    washA = res12.wells()[:5]
    washB = res12.wells()[6:11]
    elution = elut12.wells()[11]
    
    # Positions
    mag_samples_m = magplate.rows()[0][:num_cols]
    # temp_samples_m = tempplate.rows()[0][:num_cols]
    pcr_samples_m = pcr_plate.rows()[0][:num_cols]
    # -------------------------------------------------------------------------
    
    # --- Setup ---------------------------------------------------------------
    magdeck.disengage()  # just in case
    # tempdeck.set_temperature(80)
    m300.flow_rate.dispense = 150
    m300.flow_rate.blow_out = 300
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
    
    def mix(vol):
        for i, m in enumerate(mag_samples_m):
            pick_up(m300)
            m300.mix(10, 280, m.bottom(0.3))
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

    def elute(vol):
        magdeck.disengage()
        ctx.pause("Check the drying of deepwell plate.")
        
        # resuspend beads in elution
        m300.flow_rate.aspirate = ELUTE_ASPIRATION_RATE
        for i, m in enumerate(mag_samples_m):
            pick_up(m300)
            side = 1 if i % 2 == 0 else -1
            loc = m.bottom(0.5).move(Point(x=side*2))
            m300.aspirate(vol, elution)
            m300.move_to(m.center())
            m300.dispense(vol, loc)
            m300.mix(10, 30, loc)
            m300.touch_tip(v_offset=-5)
            m300.air_gap(20)
            drop(m300)
        
        for i, (m, e) in enumerate(zip(mag_samples_m, pcr_samples_m)):
            pick_up(m300)
            m300.transfer(vol, m.bottom(0.5), e.bottom(5), air_gap=20, new_tip='never')
            m300.air_gap(20)
            drop(m300)
    # -------------------------------------------------------------------------
    
    # --- RUN -----------------------------------------------------------------
    mix(mag_samples_m)
    delay(20, 'Waiting before magnetic module activation', ctx)
    magdeck.engage(height=magheight)
    delay(9, 'Incubating on magnet at room temperature', ctx)
    
    remove_supernatant(STARTING_VOL)
    wash(680, washA, 20)
    wash(680, washB, 20)
    elute(ELUTION_VOL)
    
    magdeck.disengage()
    ctx.comment("Move chilled elution plate on block (slot 1) to Station C")
    # -------------------------------------------------------------------------
