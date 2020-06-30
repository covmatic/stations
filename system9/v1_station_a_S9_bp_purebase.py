from .station import Station, labware_loader, instrument_loader
from .geometry import LysisTube
from opentrons.protocol_api import ProtocolContext
from itertools import chain, islice
import math
import os
import json
import logging
from typing import Optional, Any

_metadata = {
    'protocolName': 'Version 1 S9 Station A BP Purebase',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.0'
}


class V1StationAS9BpPurebase(Station):
    def __init__(
        self, num_samples: int, samples_per_row: int = 8, sample_volume: float = 200, lysis_volume: float = 160,
        default_aspirate: float = 100, default_dispense: float = 100, default_blow_out: float = 300,
        lysis_rate_aspirate: float = 100, lysis_rate_dispense: float = 100,
        lysis_cone_height: float = 0, lysis_headroom_height: float = 5, air_gap_sample: float = 20,
        mix_repeats: int = 5, mix_volume: float = 150,
        tip_rack: bool = False, tip_log_folder_path: str = './data/A', tip_log_filename: str = 'tip_log.json',
        metadata: dict = _metadata, logger: Optional[logging.getLoggerClass()] = None,
    ):
        """ Build a :py:class:`.V1StationAS9BpPurebase`.

        :param num_samples: The number of samples that will be loaded on the station A
        :param samples_per_row: The number of samples in a row of the destination plate
        :param sample_volume: The volume of a sample in uL
        :param lysis_volume: The volume of lysis buffer to use per sample in uL
        :param default_aspirate: P300 default aspiration flow rate in uL/s
        :param default_dispense: P300 default dispensation flow rate in uL/s
        :param default_blow_out: P300 default blow out flow rate in uL/s
        :param lysis_rate_aspirate: P300 aspiration flow rate when aspirating lysis buffer in uL/s
        :param lysis_rate_dispense: P300 dispensation flow rate when dispensing lysis buffer in uL/s
        :param lysis_cone_height: height of he conic bottom of the lysis buffer tube in mm
        :param lysis_headroom_height: headroom always to keep from the bottom of the lysis buffer tube in mm
        :param air_gap_sample: air gap for sample transfer
        :param mix_repeats: number of repetitions during mixing
        :param mix_volume: volume aspirated for mixing
        :param tip_rack: If True, try and load previous tiprack log from the JSON file
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_log_filename: file name for the tip log JSON dump
        :param metadata: protocol metadata
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        """
        self._num_samples = num_samples
        self._samples_per_row = samples_per_row
        self._sample_volume = sample_volume
        self._lysis_volume = lysis_volume
        self._tip_rack = tip_rack
        self._default_aspirate = default_aspirate
        self._default_dispense = default_dispense
        self._default_blow_out = default_blow_out
        self._lysis_rate_aspirate = lysis_rate_aspirate
        self._lysis_rate_dispense = lysis_rate_dispense
        self._lysis_cone_height = lysis_cone_height
        self._lysis_headroom_height = lysis_headroom_height
        self._air_gap_sample = air_gap_sample
        self._mix_repeats = mix_repeats
        self._mix_volume = mix_volume
        self._tip_log_folder_path = tip_log_folder_path
        self._tip_log_filename = tip_log_filename
        self.metadata = metadata
        self._logger = logger
        self._ctx = None
    
    @labware_loader(0, "_tempdeck", "_internal_control")
    def load_tempdeck(self):
        self._tempdeck = self._ctx.load_module('Temperature Module Gen2', '10')
        self._tempdeck.set_temperature(4)
        self._internal_control = self._tempdeck.load_labware(
            'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
            'chilled tubeblock for internal control (strip 1)'
        ).wells()[0]
    
    @labware_loader(1, "_source_racks")
    def load_source_racks(self):
        self._source_racks = [
            self._ctx.load_labware(
                'opentrons_24_tuberack_nest_1.5ml_screwcap', slot,
                'source tuberack ' + str(i+1)
            ) for i, slot in enumerate(['2', '3', '5', '6'])
        ]
    
    @labware_loader(2, "_dest_plate")
    def load_dest_plate(self):
        self._dest_plate = self._ctx.load_labware(
            'nest_96_wellplate_2ml_deep', '1', '96-deepwell sample plate'
        )
    
    @labware_loader(3, "_lys_buf")
    def load_lys_buf(self):
        self._lys_buff = self._ctx.load_labware(
            'opentrons_6_tuberack_falcon_50ml_conical', '4',
            '50ml tuberack for lysis buffer + PK (tube A1)'
        ).wells()[0]
    
    @labware_loader(4, "_tipracks300")
    def load_tipracks300(self):
        self._tipracks300 = [
            self._ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200ul filter tiprack')
            for slot in ['8', '9', '11']
        ]
    
    @labware_loader(5, "_tipracks20")
    def load_tipracks20(self):
        self._tipracks20 = [self._ctx.load_labware('opentrons_96_filtertiprack_20ul', '7', '20ul filter tiprack')]
    
    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=self._tipracks20)
    
    @instrument_loader(1, "_p300")
    def load_p300(self):
        self._p300 = self._ctx.load_instrument('p300_single_gen2', 'right', tip_racks=self._tipracks300)
        self._p300.flow_rate.aspirate = self._default_aspirate
        self._p300.flow_rate.dispense = self._default_dispense
        self._p300.flow_rate.blow_out = self._default_blow_out
    
    @property
    def num_rows(self) -> int:
        return math.ceil(self._num_samples/self._samples_per_row)
    
    @property
    def initlial_volume_lys(self) -> float:
        return self._num_samples * self._lysis_volume
    
    def setup_samples(self):
        self._sources = list(islice(chain.from_iterable(rack.wells() for rack in self._source_racks), self._num_samples))
        self._dests_single = self._dest_plate.wells()[:self._num_samples]
        self._dests_multi = self._dest_plate.rows()[0][:self.num_rows]
    
    @property
    def _tip_log_filepath(self) -> str:
        return os.path.join(self._tip_log_folder_path, self._tip_log_filename)
    
    def setup_tip_log(self):
        self._tip_log = {'count': {}}
        if self._tip_rack and not self._ctx.is_simulating():
            self.logger.debug("logging tip info in {}".format(self._tip_log_filepath))
            if os.path.isfile(self._tip_log_filepath):
                with open(self._tip_log_filepath) as json_file:
                    data: dict = json.load(json_file)
                    self._tip_log['count'][self._p300] = data.get('tips300', 0)
                    self._tip_log['count'][self._m20] = data.get('tips20', 0)
        else:
            self.logger.debug("not using tip log file")
            self._tip_log['count'] = {self._p300: 0, self._m20: 0}
        
        self._tip_log['tips'] = dict(zip(
            (self._p300, self._m20),
            map(lambda tiprack: list(chain.from_iterable(rack.rows()[0] for rack in tiprack)), (self._tipracks300, self._tipracks20))
        ))
        self._tip_log['max'] = {p: len(l) for p, l in self._tip_log['tips'].items()}
    
    def setup_lys_tube(self):
        self._lysis_tube = LysisTube(self._lys_buff.diameter / 2, self._lysis_cone_height)
        self._lysis_tube.height = self._lysis_headroom_height
        self._lysis_tube.fill(self.initlial_volume_lys)
        self.logger.info("number of samples: {}. Lysis buffer expected volume: {} uL".format(self._num_samples, math.ceil(self._lysis_tube.volume)))
        self.logger.debug("lysis buffer expected height: {:.2f} mm".format(self._lysis_tube.height))
    
    def pick_up(self, pip):
        if self._tip_log['count'][pip] == self._tip_log['max'][pip]:
            # If empty, wait for refill
            self._ctx.pause('Replace {:.0f} uL tipracks before resuming.'.format(pip.max_volume))
            pip.reset_tipracks()
            self._tip_log['count'][pip] = 0
        pip.pick_up_tip(self._tip_log['tips'][pip][self._tip_log['count'][pip]])
        self._tip_log['count'][pip] += 1
    
    def transfer_sample(self, source, dest):
        self.logger.debug("transferring from {} to {}".format(source, dest))
        self.pick_up(self._p300)
        self._p300.mix(self._mix_repeats, self._mix_volume, source.bottom(2))
        self._p300.transfer(
            self._sample_volume,
            source.bottom(self._lysis_headroom_height), dest.bottom(self._lysis_headroom_height),
            air_gap=self._air_gap_sample, new_tip='never'
        )
        self._p300.air_gap(self._air_gap_sample)
        self._p300.drop_tip()
    
    def transfer_lys(self, dest):
        self.logger.debug("transferring lysis to {}".format(dest))
        self.pick_up(self._p300)
        self._p300.transfer(
            self._lysis_volume,
            self._lys_buff.bottom(max(self._lysis_tube.extract(self._lysis_volume), self._lysis_headroom_height)),
            dest.bottom(self._lysis_headroom_height), air_gap=self._air_gap_sample, mix_after=(10, 100), new_tip='never'
        )
        self._p300.air_gap(self._air_gap_sample)
        self._p300.drop_tip()
    
    def transfer_internal_control(self, dest):
        self.logger.debug("transferring internal control to {}".format(dest))
        self.pick_up(self._m20)
        self._m20.transfer(10, self._internal_control, dest.bottom(10), air_gap=5, new_tip='never')
        self._m20.mix(5, 20, dest.bottom(2))
        self._m20.air_gap(5)
        self._m20.drop_tip()
    
    def track_tip(self):
        if not self._ctx.is_simulating():
            self.logger.debug("dumping logging tip info in {}".format(self._tip_log_filepath))
            if not os.path.isdir(self._tip_log_folder_path):
                os.mkdir(self._tip_log_folder_path)
            data = {
                'tips300': self._tip_log['count'][self._p300],
                'tips20': self._tip_log['count'][self._m20]
            }
            with open(self._tip_log_filepath, 'w') as outfile:
                json.dump(data, outfile)
    
    def run(self, ctx: ProtocolContext):
        self._ctx = ctx
        self.load_labware()
        self.load_instruments()
        self.setup_samples()
        self.setup_tip_log()
        self.setup_lys_tube()
        
        for s, d in zip(self._sources, self._dests_single):
            self.transfer_sample(s, d)
        
        self._p300.flow_rate.aspirate = self._lysis_rate_aspirate
        self._p300.flow_rate.dispense = self._lysis_rate_dispense
        for d in self._dests_single:
            self.transfer_lys(d)
        
        self.logger.info('incubate sample plate (slot 4) at 55-57°C for 20 minutes. Return to slot 4 when complete.')
        self._ctx.pause('Pausing')
        
        for d in self._dests_multi:
            self.transfer_internal_control(d)
        
        self.logger.info('move deepwell plate (slot 4) to Station B for RNA extraction.')
        self.track_tip()


station_a = V1StationAS9BpPurebase(num_samples=96)
metadata = station_a.metadata
run = station_a.run


if __name__ == "__main__":
    from opentrons import simulate
    station_a.metadata["apiLevel"] = "2.3"
    
    run(simulate.get_protocol_api(station_a.apiLevel))
