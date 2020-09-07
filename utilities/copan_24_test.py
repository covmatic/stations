from opentrons.protocol_api import ProtocolContext, InstrumentContext


metadata = {
    "apiLevel": "2.3",
    "author": "Marco",
    "description": "Custom Copan x24 rack test"
}


class pick_up_tip:
    def __init__(self, pip: InstrumentContext):
        self._pip = pip
    
    def __enter__(self):
        self._pip.pick_up_tip()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._pip.drop_tip()
        if isinstance(exc_val, Exception):
            raise exc_val


def run(ctx: ProtocolContext):
    ctx.comment("Test the custom Copan x24 rack")
    
    rack = ctx.load_labware('copan_24_tuberack_14000ul', '2', 'custom tuberack')
    tipracks1000 = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', '1', '1000µl filter tiprack')]
    p1000 = ctx.load_instrument('p1000_single_gen2', 'right', tip_racks=tipracks1000)
    
    with pick_up_tip(p1000):
        for w in rack.wells():
            ctx.pause("moving to top of {}".format(w))
            p1000.move_to(w.top())
            ctx.pause("moving to bottom of {} (1 mm high)".format(w))
            p1000.move_to(w.bottom(1))
            p1000.aspirate(5)
            p1000.dispense(5)
