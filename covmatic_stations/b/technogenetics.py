from opentrons.protocol_api.labware import Well

from .b import StationB, labware_loader
from typing import Tuple, List
from opentrons.types import Point
from ..utils import get_labware_json_from_filename, mix_bottom_top, WellWithVolume


class StationBTechnogenetics(StationB):
    _protocol_description = "station B protocol for Technogenetics kit"

    def __init__(self,
                 beads_drying_time: float = 5,
                 elute_mix_times: int = 0,
                 elution_vol: float = 50,
                 elute_incubate: bool = False,
                 final_mix_height: float = 0.5,
                 final_mix_times: int = 5,
                 final_mix_vol: float = 20,
                 final_mix_blow_out_height: float = -2,
                 final_transfer_rate_aspirate: float = 30,
                 final_transfer_rate_dispense: float = 30,
                 final_transfer_side: float = 0.5,
                 final_transfer_dw_bottom_height: float = 0.6,
                 final_vol: float = 20,
                 flatplate_slot: str = '3',
                 incubation_temperature: float = 55,
                 incubation_time: float = 20,
                 h_bottom: float = 1,
                 n_bottom: float = 3,
                 mix_incubate_on_time: float = 20,
                 mix_incubate_off_time: float = 5,
                 postspin_incubation_time: float = 0.5,
                 remove_wash_vol: float = 50,
                 sample_mix_height: float = 1,
                 sample_mix_times: int = 10,
                 sample_mix_vol: float = 180,
                 sample_vertical_speed: float = 35,
                 mix_samples_rate = 200,
                 mix_samples_last_rate = 94,
                 starting_vol: float = 650,
                 supernatant_removal_aspiration_rate_first_phase = 94,
                 tempdeck_slot: str = '10',
                 tempdeck_temp: float = None,
                 tempdeck_auto_turnon: bool = False,
                 tempdeck_auto_turnoff: bool = True,
                 thermomixer_incubation_time: float = 0.5,
                 tipracks_slots: Tuple[str, ...] = ('4', '6', '7', '8', '9'),
                 wash_1_vol: float = 650,
                 wash_2_vol: float = 650,
                 wash_headroom: float = 1.05,
                 wash_mix_vol: float = 180,
                 wash_mix_walk: bool = True,
                 watchdog_serial_timeout_seconds: int = 30,
                 **kwargs
                 ):
        """ Build a :py:class:`.StationBTechnogenetics`.
        :param beads_drying_time: [minutes] time to wait for beads to try in air
        :param external_deepwell_incubation: whether or not to perform deepwell incubation outside the robot
        :param final_mix_height: Mixing height (from the bottom) for final transfer in mm
        :param final_mix_times: Mixing repetitions for final transfer
        :param final_mix_vol: Mixing volume for final transfer in uL
        :param final_transfer_rate_aspirate: Aspiration rate during final transfer in uL/s
        :param final_transfer_rate_dispense: Dispensation rate during final transfer in uL/s
        :param final_vol: Volume to transfer to the PCR plate in uL
        :param incubation_temperature: Temperature set on temperature module to incubate samples in °C
        :param incubation_time: minutes to wait on temperature module to incubate samples
        :param mix_incubate_on_time: Time for incubation on magnet after mix in minutes
        :param mix_incubate_off_time: Time for incubation off magnet after mix in minutes
        :param postspin_incubation_time: Post-spin incubation time in minutes
        :param remove_wash_vol: Volume to remove during wash removal in uL
        :param sample_mix_times: Mixing height for samples in mm from the bottom
        :param sample_mix_times: Mixing repetitions for samples
        :param sample_mix_vol: Mixing volume for samples in uL
        :param sample_vertical_speed: speed of vertical movement exiting well
        :param thermomixer_incubation_time: Time for incubation after thermomixer in minutes
        """
        super(StationBTechnogenetics, self).__init__(
            elute_mix_times=elute_mix_times,
            elution_vol=elution_vol,
            elute_incubate=elute_incubate,
            flatplate_slot=flatplate_slot,
            starting_vol=starting_vol,
            supernatant_removal_aspiration_rate_first_phase = supernatant_removal_aspiration_rate_first_phase,
            tempdeck_slot=tempdeck_slot,
            tempdeck_temp=tempdeck_temp,
            tempdeck_auto_turnon=tempdeck_auto_turnon,
            tempdeck_auto_turnoff=tempdeck_auto_turnoff,
            tipracks_slots=tipracks_slots,
            wash_1_vol=wash_1_vol,
            wash_2_vol=wash_2_vol,
            wash_headroom=wash_headroom,
            wash_mix_vol=wash_mix_vol,
            wash_mix_walk=wash_mix_walk,
            **kwargs
        )
        self._beads_drying_time = beads_drying_time
        self._final_mix_blow_out_height = final_mix_blow_out_height
        self._final_mix_height = final_mix_height
        self._final_mix_times = final_mix_times
        self._final_transfer_side = final_transfer_side
        self._final_transfer_dw_bottom_height = final_transfer_dw_bottom_height
        self._final_mix_vol = final_mix_vol
        self._final_transfer_rate_aspirate = final_transfer_rate_aspirate
        self._final_transfer_rate_dispense = final_transfer_rate_dispense
        self._mix_samples_rate = mix_samples_rate
        self._mix_samples_last_rate = mix_samples_last_rate
        self._final_vol = final_vol
        self._flatplate_slot = flatplate_slot
        self._incubation_temperature = incubation_temperature
        self._incubation_time = incubation_time
        self._h_bottom = h_bottom
        self._n_bottom = n_bottom
        self._mix_incubate_on_time = mix_incubate_on_time
        self._mix_incubate_off_time = mix_incubate_off_time
        self._postspin_incubation_time = postspin_incubation_time
        self._remove_wash_vol = remove_wash_vol
        self._sample_mix_height = sample_mix_height
        self._sample_mix_times = sample_mix_times
        self._sample_mix_vol = sample_mix_vol
        self._sample_vertical_speed = sample_vertical_speed
        self._thermomixer_incubation_time = thermomixer_incubation_time
        self._watchdog_serial_timeout_seconds = watchdog_serial_timeout_seconds
    
    @labware_loader(5, "_flatplate")
    def load_flatplate(self):
        self._flatplate = self._ctx.load_labware('opentrons_96_aluminumblock_nest_wellplate_100ul', self._flatplate_slot, 'chilled elution plate on block for Station C')
    
    @labware_loader(5, "_tempplate")
    def load_tempplate(self):
        self._tempplate = self._tempdeck.load_labware(self._magplate_model)

    @labware_loader(6, "_waste")
    def load_waste(self):
        self._waste = self._ctx.load_labware_from_definition(
            get_labware_json_from_filename("biofil_1_reservoir_500000ul.json"), '11', 'Liquid Waste').wells()[0].top()

    @property
    def pcr_samples_m(self):
        return self._flatplate.rows()[0][:self.num_cols]
    
    @property
    def temp_samples_m(self):
        return self._tempplate.rows()[0][:self.num_cols]
    
    def load_etoh(self): pass

    @labware_loader(9, "_elut12")
    def load_elut12(self):
        self._elut12 = self._ctx.load_labware('nest_12_reservoir_15ml', '2', 'Trough with Wash B and Elution')

    @property
    def water(self):
        return self._elut12.wells()[11]

    @property
    def wash1(self):
        return self._res12.wells()[:6]
    
    @property
    def wash2(self):
        return self._elut12.wells()[:6]

    @staticmethod
    def wash_getcol(sample_col_idx: int, wash_cols: int, source):
        return source[sample_col_idx // 2]

    def mix_samples(self,  wells: List[Well], stage_name: str = "mix sample"):
        for i, m in enumerate(wells):
            if self.run_stage("{} {}/{}".format(stage_name, i + 1, len(wells))):
                self._m300.flow_rate.aspirate = self._mix_samples_rate
                self._m300.flow_rate.dispense = self._mix_samples_rate

                well_with_volume = WellWithVolume(m,
                                                  initial_vol=self._starting_vol - self._sample_mix_vol,
                                                  min_height=self._sample_mix_height,
                                                  headroom_height=0)
                self.pick_up(self._m300)
                mix_bottom_top(pip=self._m300,
                               reps=self._sample_mix_times,
                               vol=self._sample_mix_vol,
                               pos=m.bottom,
                               bottom=self._sample_mix_height,
                               top=well_with_volume.height,
                               last_dispense_rate=self._mix_samples_last_rate)

                self._m300.move_to(m.top(0), speed=self._sample_vertical_speed)
                self._m300.air_gap(self._bind_air_gap)
                self.drop(self._m300)

    def incubate_and_mix(self):
        self.tempdeck_set_temperature(self._incubation_temperature)

        self.delay_start_count()
        self.mix_samples(self.temp_samples_m)

        if self.run_stage("incubation"):
            self.delay_wait_to_elapse(minutes=self._incubation_time)

        self.tempdeck_deactivate()

    def elute(self, positions=None, transfer: bool = False, stage: str = "elute"):
        if positions is None:
            positions = self.temp_samples_m
        self.set_magdeck(False)
        super(StationBTechnogenetics, self).elute(positions=positions, transfer=transfer, stage=stage)
    
    def remove_wash(self, vol, stage: str = "remove wash"):
        self.remove_supernatant(vol, stage)

    def final_transfer(self):
        self.set_magdeck(True)
        self.set_flow_rate(aspirate=self._final_transfer_rate_aspirate, dispense=self._final_transfer_rate_dispense)
        self.final_transfer_movements()

    def final_transfer_movements(self):
        n = len(list(zip(self.mag_samples_m, self.pcr_samples_m)))
        for i, (m, e) in enumerate(zip(self.mag_samples_m, self.pcr_samples_m)):
            if self.run_stage("final transfer {}/{}".format(i + 1, n)):
                self.pick_up(self._m300)
                side = -1 if i % 2 == 0 else 1
                loc = m.bottom(self._final_transfer_dw_bottom_height).move(Point(x=side*self._final_transfer_side))
                self._m300.aspirate(self._final_vol, loc)
                self._m300.air_gap(self._elute_air_gap)
                self._m300.dispense(self._elute_air_gap, e.top())
                self._m300.dispense(self._m300.current_volume, e.bottom(self._final_mix_height))

                #self._m300.transfer(self._final_vol, loc, e.bottom(self._elution_height), air_gap=self._elute_air_gap, new_tip='never')
                self._m300.mix(self._final_mix_times, self._final_mix_vol, e.bottom(self._final_mix_height))
                self._m300.blow_out(e.top(self._final_mix_blow_out_height))
                self._m300.air_gap(self._elute_air_gap)
                self.drop(self._m300)

    def spin(self, stage_name: str):
        if self.run_stage("spin deepwell {}".format(stage_name)):
            self.set_magdeck(False)
            self.dual_pause("spin the deepwell", between=self.set_external)
            self.set_internal()

    def second_removal(self, stage_name: str):
        if self.run_stage("post spin incubation {}".format(stage_name)):
            self.set_magdeck(True)
            self.delay(self._postspin_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))
        self.remove_wash(self._remove_wash_vol, "remove {} after spin".format(stage_name))

    def spin_and_remove(self, stage_name: str):
        self.spin(stage_name)
        self.second_removal(stage_name)

    def set_flow_rate(self, aspirate: float = None, dispense: float = None):
        if aspirate is not None:
            self._m300.flow_rate.aspirate = aspirate
        if dispense is not None:
            self._m300.flow_rate.dispense = dispense

    def body(self):
        self.logger.info(self.get_msg_format("volume", "wash 1", self._wash_headroom * self._wash_1_vol * self._num_samples / 1000))
        self.logger.info(self.get_msg_format("volume", "wash 2", self._wash_headroom * self._wash_2_vol * self._num_samples / 1000))
        self.logger.info(self.get_msg_format("volume", "elution buffer", self._wash_headroom * self._elution_vol * self._num_samples / 1000))

        self.incubate_and_mix()

        if self.run_stage("mix incubate off"):
            self.pause("move plate to magdeck")
            self.set_magdeck(True)
            self.delay(self._mix_incubate_off_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))

        self.remove_supernatant(self._starting_vol)

        self.wash(self._wash_1_vol, self.wash1, self._wash_1_times, "wash A")

        self.spin("wash A")

        if self.run_stage("add wash B and elute"):
            self.pause("Add wash B and elute buffer in slot {}{}".format(
                self.wash2[0].parent,
                " and {}".format(self.water.parent) if self.wash2[0].parent != self.water.parent else ""))

        self.second_removal("wash A")

        self.wash(self._wash_2_vol, self.wash2, self._wash_2_times, "wash B")
        self.spin_and_remove("wash B")

        if self._tempdeck_temp is not None and not self._tempdeck_auto_turnon:
            # self._tempdeck.start_set_temperature(self._tempdeck_temp)
            self.tempdeck_set_temperature(self._tempdeck_temp)

        if self.run_stage("beads drying"):
            self.set_magdeck(False)
            self.delay(self._beads_drying_time, msg="beads drying")

        self.elute(self.mag_samples_m)

        if self.run_stage("thermomixer"):
            self.dual_pause("seal the deepwell", between=self.set_external)
            self.set_internal()

        if self.run_stage("input PCR"):
            self.pause("input PCR")

        if self.run_stage("post thermomixer incubation"):
            self.set_magdeck(True)
            self.delay(self._thermomixer_incubation_time, self.get_msg_format("incubate on magdeck", self.get_msg("on")))

        self.final_transfer()

        self.set_magdeck(False)
        self.logger.info(self.msg_format("move to PCR"))

    def tempdeck_set_temperature(self, temperature):
        self.watchdog_reset(self._watchdog_serial_timeout_seconds)
        self._tempdeck.start_set_temperature(temperature)
        self.watchdog_stop()

    def tempdeck_deactivate(self):
        self.watchdog_reset(self._watchdog_serial_timeout_seconds)
        self._tempdeck.deactivate()
        self.watchdog_stop()


class StationBTechnogeneticsSaliva(StationBTechnogenetics):
    def __init__(self,
                 incubation_heatup_time: float = 15,
                 incubation_mixing_time: float = 10,
                 incubation_mix_times: int = 2,
                 *args,
                 **kwargs):
        """ Build a :py:class:`.StationBTechnogeneticsSaliva`.
            :param incubation_heatup_time: minutes needed to warm up the deepwell plate to the incubation temperature (experimentally found)
            :param incubation_mixing_time: minutes of incubation during mix
            :param incubation_mix_times: number of mix during incubation
        """
        super(StationBTechnogeneticsSaliva, self).__init__(*args, **kwargs)
        self._incubation_heatup_time = incubation_heatup_time
        self._incubation_mixing_time = incubation_mixing_time
        self._incubation_mix_times = incubation_mix_times

    def incubate_and_mix(self):
        self.tempdeck_set_temperature(self._incubation_temperature)

        if self.run_stage("initial incubation"):
            self.delay(self._incubation_heatup_time)

        for i in range(self._incubation_mix_times):
            self.delay_start_count()
            self.mix_samples(self.temp_samples_m, "mix samples {}".format(i+1))
            if self.run_stage("incubation after mix {}".format(i+1)):
                self.delay_wait_to_elapse(minutes=self._incubation_mixing_time)

        self.tempdeck_deactivate()


if __name__ == "__main__":
    StationBTechnogenetics(metadata={'apiLevel': '2.3'}).simulate()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
