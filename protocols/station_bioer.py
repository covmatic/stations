import logging
from covmatic_stations.Bioer.Bioer_full_dw import BioerProtocol


logging.getLogger(BioerProtocol.__name__).setLevel(logging.INFO)
metadata = {'apiLevel': '2.7'}
station = BioerProtocol(num_samples = 96,
                        transfer_proteinase_phase = True, mix_beads_phase = False, mastermix_phase = True, transfer_elutes_phase = False,
                        control_well_positions = ['G12', 'H12'],
                        pk_tube_bottom_height = 2, mm_tube_bottom_height = 5, pcr_bottom_headroom_height = 4.5, dw_bottom_height = 13.5,
                        vertical_offset = -16,
                        pk_volume_tube = 320, vol_pk_offset = 5, vol_mm_offset = 10)


def run(ctx):
    return station.run(ctx)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
