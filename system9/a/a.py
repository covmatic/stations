from .. import __version__
from ..station import Station, labware_loader, instrument_loader
from ..geometry import LysisTube
from opentrons.protocol_api import ProtocolContext
from itertools import chain, islice, repeat
import math
import os
import json
import logging
from typing import Optional, Tuple


_metadata = {
    'protocolName': 'Version 1 S9 Station A BP Purebase',
    'author': 'Nick <protocols@opentrons.com>',
    'refactoring': 'Marco <marcotiraboschi@hotmail.it>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


class StationA(Station):    
    def __init__(
        self,
        air_gap_dest_multi: float = 5,
        air_gap_sample: float = 20,
        default_aspirate: float = 25,
        default_blow_out: float = 300,
        default_dispense: float = 25,
        dest_headroom_height: float = 5,
        dest_multi_headroom_height: float = 2,
        hover_height: float = -2,
        ic_capacity: float = 180,
        ic_headroom: float = 1.1,
        ic_headroom_bottom: float = 2,
        ic_mix_repeats: int = 5,
        ic_mix_volume: float = 20,
        iec_volume: float = 20,
        internal_control_idx_th: int = 48,
        logger: Optional[logging.getLoggerClass()] = None,
        lysis_cone_height: float = 16,
        lysis_headroom_height: float = 5,
        lysis_rate_aspirate: float = 100,
        lysis_rate_dispense: float = 100,
        lysis_volume: float = 160,
        lys_mix_repeats: int = 10,
        lys_mix_volume: float = 100,
        main_pipette: str = 'p300_single_gen2',
        main_tiprack: str = 'opentrons_96_tiprack_300ul',
        main_tiprack_label: str = '200ul filter tiprack',
        max_speeds_a: float = 20,
        metadata: dict = _metadata,
        mix_repeats: int = 5,
        mix_volume: float = 150,
        num_samples: int = 96,
        samples_per_col: int = 8,
        sample_volume: float = 200,
        source_headroom_height: float = 8,
        source_position_top: float = 10,
        source_racks: str = 'opentrons_24_tuberack_nest_1.5ml_screwcap',
        source_racks_definition_filepath: str = "",
        source_racks_slots: Tuple[str, ...] = ('2', '3', '5', '6'),
        tempdeck_temp: float = 4,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/A',
        tip_rack: bool = False,
        tipracks_slots: Tuple[str, ...] = ('8', '9', '11'),
        jupyter: bool = True,
    ):
        """ Build a :py:class:`.StationA`.

        :param air_gap_dest_multi: air gap for destination tube (multi) in uL
        :param air_gap_sample: air gap for sample transfer in uL
        :param default_aspirate: P300 default aspiration flow rate in uL/s
        :param default_blow_out: P300 default blow out flow rate in uL/s
        :param default_dispense: P300 default dispensation flow rate in uL/s
        :param dest_headroom_height: headroom always to keep from the bottom of the destination tube in mm
        :param dest_multi_headroom_height: headroom always to keep from the bottom of the destination tube (multi) in mm
        :param hover_height: height from the top at which to hover (should be negative) in mm
        :param ic_capacity: capacity of the internal control tube
        :param ic_headroom: headroom for the internal control tube (multiplier)
        :param ic_headroom_bottom: headroom always to keep from the bottom of the internal control tube in mm
        :param ic_mix_repeats: number of repetitions during mixing the internal control
        :param ic_mix_volume: volume aspirated for mixing the internal control in uL
        :param iec_volume: The volume of lysis buffer to use per sample in uL
        :param internal_control_idx_th: internal control index threshold for choosing the strip 
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param lysis_cone_height: height of he conic bottom of the lysis buffer tube in mm
        :param lysis_headroom_height: headroom always to keep from the bottom of the lysis buffer tube in mm
        :param lysis_rate_aspirate: P300 aspiration flow rate when aspirating lysis buffer in uL/s
        :param lysis_rate_dispense: P300 dispensation flow rate when dispensing lysis buffer in uL/s
        :param lysis_volume: The volume of lysis buffer to use per sample in uL
        :param lys_mix_repeats: number of repetitions during mixing the lysis buffer
        :param lys_mix_volume: volume aspirated for mixing the lysis buffer in uL
        :param main_pipette: type of the main pipette
        :param main_tiprack: type of the main tiprack
        :param main_tiprack_label: label of the main tiprack
        :param mix_repeats: number of repetitions during mixing
        :param mix_volume: volume aspirated for mixing in uL
        :param max_speeds_a: max speed for sample transfer
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station A
        :param samples_per_col: The number of samples in a column of the destination plate
        :param sample_volume: The volume of a sample in uL
        :param source_headroom_height: headroom always to keep from the bottom of the source tube in mm
        :param source_position_top: height from the top of the source tube in mm
        :param source_racks: source racks to load
        :param source_racks_definition_filepath: filepath for source racks definitions
        :param source_racks_slots: slots where source racks are installed
        :param tempdeck_temp: tempdeck temperature in Celsius degrees
        :param tip_log_filename: file name for the tip log JSON dump
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_rack: If True, try and load previous tiprack log from the JSON file
        :param jupyter: Specify whether the protocol is run on Jupyter (or Python) instead of the robot
        """
        self._ic_headroom_bottom = ic_headroom_bottom
        self._ic_capacity = ic_capacity
        self._ic_headroom = ic_headroom
        self._main_pipette = main_pipette
        self._main_tiprack = main_tiprack
        self._main_tiprack_label = main_tiprack_label
        self._source_racks_definition_filepath = source_racks_definition_filepath
        self._tempdeck_temp = tempdeck_temp
        self._num_samples = num_samples
        self._samples_per_col = samples_per_col
        self._sample_volume = sample_volume
        self._lysis_volume = lysis_volume
        self._iec_volume = iec_volume
        self._tip_rack = tip_rack
        self._default_aspirate = default_aspirate
        self._default_dispense = default_dispense
        self._default_blow_out = default_blow_out
        self._lysis_rate_aspirate = lysis_rate_aspirate
        self._lysis_rate_dispense = lysis_rate_dispense
        self._lysis_cone_height = lysis_cone_height
        self._lysis_headroom_height = lysis_headroom_height
        self._air_gap_sample = air_gap_sample
        self._source_headroom_height = source_headroom_height
        self._source_position_top = source_position_top
        self._internal_control_idx_th = internal_control_idx_th
        self._dest_headroom_height = dest_headroom_height
        self._dest_multi_headroom_height = dest_multi_headroom_height
        self._air_gap_dest_multi = air_gap_dest_multi
        self._hover_height = hover_height
        self._max_speeds_a = max_speeds_a
        self._mix_repeats = mix_repeats
        self._mix_volume = mix_volume
        self._lys_mix_repeats = lys_mix_repeats
        self._lys_mix_volume = lys_mix_volume
        self._ic_mix_repeats = ic_mix_repeats
        self._ic_mix_volume = ic_mix_volume
        self._source_racks = source_racks
        self._source_racks_slots = source_racks_slots
        self._tipracks_slots = tipracks_slots
        self._tip_log_folder_path = tip_log_folder_path
        self._tip_log_filename = tip_log_filename
        self.metadata = metadata
        self._logger = logger
        self._ctx = None
        self.jupyter = jupyter
    
    @labware_loader(0, "_tempdeck", "_internal_control_strips")
    def load_tempdeck(self):
        self._tempdeck = self._ctx.load_module('Temperature Module Gen2', '10')
        self._tempdeck.set_temperature(self._tempdeck_temp)
        self._internal_control_strips = self._tempdeck.load_labware(
            'opentrons_96_aluminumblock_generic_pcr_strip_200ul',
            'chilled tubeblock for internal control (strip 1)'
        ).rows()[0][:self.num_ic_strips]
        self.logger.info("using {} internal control strips with {} uL each".format(self.num_ic_strips, self.cols_per_strip * self._iec_volume * self._ic_headroom))
    
    def _load_source_racks(self):
        self._source_racks = [
            self._ctx.load_labware(
                self._source_racks, slot,
                'source tuberack ' + str(i + 1)
            ) for i, slot in enumerate(self._source_racks_slots)
        ]
    
    @labware_loader(1, "_source_racks")
    def load_source_racks(self):
        self.logger.debug("using source racks '{}'".format(self._source_racks))
        self._load_source_racks()
    
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
    
    @labware_loader(4, "_tipracks_main")
    def load_tipracks_main(self):
        self._tipracks_main = [
            self._ctx.load_labware(self._main_tiprack, slot, self._main_tiprack_label)
            for slot in self._tipracks_slots
        ]
        self.logger.debug("main tipracks: {}".format(", ".join(map(str, self._tipracks_main))))
    
    @labware_loader(5, "_tipracks20")
    def load_tipracks20(self):
        self._tipracks20 = [self._ctx.load_labware('opentrons_96_filtertiprack_20ul', '7', '20ul filter tiprack')]
    
    @instrument_loader(0, "_m20")
    def load_m20(self):
        self._m20 = self._ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=self._tipracks20)
    
    @instrument_loader(1, "_p_main")
    def load_p_main(self):
        self._p_main = self._ctx.load_instrument(self._main_pipette, 'right', tip_racks=self._tipracks_main)
        self._p_main.flow_rate.aspirate = self._default_aspirate
        self._p_main.flow_rate.dispense = self._default_dispense
        self._p_main.flow_rate.blow_out = self._default_blow_out
        self.logger.debug("main pipette: {}".format(self._p_main))
    
    @property
    def num_cols(self) -> int:
        return math.ceil(self._num_samples/self._samples_per_col)
    
    @property
    def num_ic_strips(self) -> int:
        return math.ceil(self._iec_volume * self.num_cols * self._ic_headroom / self._ic_capacity)
    
    @property
    def cols_per_strip(self) -> int:
        return math.ceil(self.num_cols / self.num_ic_strips)
    
    @property
    def initlial_volume_lys(self) -> float:
        return self._num_samples * self._lysis_volume
    
    def setup_samples(self):
        self._sources = list(islice(chain.from_iterable(rack.wells() for rack in self._source_racks), self._num_samples))
        self._dests_single = self._dest_plate.wells()[:self._num_samples]
        self._dests_multi = self._dest_plate.rows()[0][:self.num_cols]
    
    @property
    def _tip_log_filepath(self) -> str:
        return os.path.join(self._tip_log_folder_path, self._tip_log_filename)
    
    def _tiprack_log_args(self):
        # first of each is the m20, second the main pipette
        return ('m20', self._main_pipette), (self._m20, self._p_main), (self._tipracks20, self._tipracks_main)
    
    def setup_tip_log(self):
        labels, pipettes, tipracks = self._tiprack_log_args()
        
        self._tip_log = {'count': {}}
        if self._tip_rack and not self._ctx.is_simulating():
            self.logger.debug("logging tip info in {}".format(self._tip_log_filepath))
            if os.path.isfile(self._tip_log_filepath):
                with open(self._tip_log_filepath) as json_file:
                    data: dict = json.load(json_file)
                    for p, l in zip(pipettes, labels):
                        self._tip_log['count'][p] = data.get(l, 0)
        else:
            self.logger.debug("not using tip log file")
            self._tip_log['count'] = dict(zip(pipettes, repeat(0)))
        
        self._tip_log['tips'] = {
            pipettes[0]: list(chain.from_iterable(rack.rows()[0] for rack in tipracks[0])),
            pipettes[1]: list(chain.from_iterable(rack.wells() for rack in tipracks[1])),
        }
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
        self.pick_up(self._p_main)
        
        self._p_main.move_to(source.top(self._source_position_top))
        self._ctx.max_speeds['A'] = self._max_speeds_a
        
        self._p_main.mix(self._mix_repeats, self._mix_volume, source.bottom(self._source_headroom_height))
        self._p_main.aspirate(self._sample_volume, source.bottom(self._source_headroom_height))        
        self._p_main.air_gap(self._air_gap_sample)
        
        self._ctx.max_speeds['A'] = None
        self._p_main.dispense(self._air_gap_sample, dest.top(self._hover_height))
        self._p_main.dispense(self._sample_volume, dest.bottom(self._dest_headroom_height))
        self._p_main.air_gap(self._air_gap_sample)
        
        self._p_main.drop_tip()
    
    def transfer_samples(self):
        for s, d in zip(self._sources, self._dests_single):
            self.transfer_sample(s, d)
    
    def transfer_lys(self, dest):
        self.logger.debug("transferring lysis to {}".format(dest))
        self.pick_up(self._p_main)
        h = max(self._lysis_tube.extract(self._lysis_volume), self._lysis_headroom_height)
        self.logger.debug("going {} mm deep".format(h))
        self._p_main.transfer(
            self._lysis_volume,
            self._lys_buff.bottom(h),
            dest.bottom(self._lysis_headroom_height), air_gap=self._air_gap_sample,
            mix_after=(self._lys_mix_repeats, self._lys_mix_volume), new_tip='never',
        )
        self._p_main.air_gap(self._air_gap_sample)
        self._p_main.drop_tip()
    
    def transfer_internal_control(self, idx: int, dest):
        strip_ind = idx // self.cols_per_strip
        self.logger.debug("transferring internal control strip {}/{} to {}".format(strip_ind + 1, self.num_ic_strips, dest))
        internal_control = self._internal_control_strips[strip_ind]
        self.pick_up(self._m20)
        # no air gap to use 1 transfer only avoiding drop during multiple transfers
        self._m20.transfer(self._iec_volume, internal_control, dest.bottom(self._ic_headroom_bottom), new_tip='never')
        self._m20.mix(self._ic_mix_repeats, self._ic_mix_volume, dest.bottom(self._dest_multi_headroom_height))
        self._m20.air_gap(self._air_gap_dest_multi)
        self._m20.drop_tip()
    
    def track_tip(self):
        labels, pipettes, tipracks = self._tiprack_log_args()
        if not self._ctx.is_simulating():
            self.logger.debug("dumping logging tip info in {}".format(self._tip_log_filepath))
            if not os.path.isdir(self._tip_log_folder_path):
                os.mkdir(self._tip_log_folder_path)
            data = dict(zip(labels, map(self._tip_log['count'].__getitem__, pipettes)))
            with open(self._tip_log_filepath, 'w') as outfile:
                json.dump(data, outfile)
    
    def run(self, ctx: ProtocolContext):
        self._ctx = ctx
        self.logger.info(self._protocol_description)
        self.logger.info("using system9 version {}".format(__version__))
        self.load_labware()
        self.load_instruments()
        self.setup_samples()
        self.setup_tip_log()
        self.setup_lys_tube()
        
        self.transfer_samples()
        
        self._p_main.flow_rate.aspirate = self._lysis_rate_aspirate
        self._p_main.flow_rate.dispense = self._lysis_rate_dispense
        for d in self._dests_single:
            self.transfer_lys(d)
        
        self.logger.info('incubate sample plate (slot 4) at 55-57°C for 20 minutes. Return to slot 4 when complete.')
        self._ctx.pause('Pausing')
        
        for i, d in enumerate(self._dests_multi):
            self.transfer_internal_control(i, d)
        
        self.logger.info('move deepwell plate (slot 1) to Station B for RNA extraction.')
        self.track_tip()
