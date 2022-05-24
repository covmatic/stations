import json
import os
import time

from opentrons.protocol_api import ProtocolContext, InstrumentContext, PairedInstrumentContext
from opentrons.protocol_api.labware import Well
from opentrons.types import Location
import logging
import math
import requests
from itertools import tee, cycle, islice, chain, repeat
from typing import Tuple, Union, Iterable, Callable, Optional, Dict, Any


class ProtocolContextLoggingHandler(logging.Handler):
    """Logging Handler that emits logs through the ProtocolContext comment method"""
    def __init__(self, ctx: ProtocolContext, *args, **kwargs):
        super(ProtocolContextLoggingHandler, self).__init__(*args, **kwargs)
        self._ctx = ctx
    
    def emit(self, record):
        try:
            self._ctx.comment(self.format(record))
        except Exception:
            self.handleError(record)


class LocalWebServerLogger:
    def __init__(self, ip: Optional[str] = None, endpoint: str = ":5002/log", timeout: float = 2,
                 errorlogger: logging.Logger = logging.getLogger("LWSLog"), *args, **kwargs):
        super(LocalWebServerLogger, self).__init__(*args, **kwargs)
        self.ip = ip
        self.endpoint = endpoint
        self.timeout = timeout
        self.level = 0
        self.last_dollar = None
        self.logfail_count = dict()  # dictionary of url, Number of exceptions during log
        self.logfail_max = 5       # Retries sending log, after that disable send.
        self.errorlogger = errorlogger
    
    @property
    def url(self) -> str:
        return "http://{}{}".format(self.ip, self.endpoint)
    
    def format(self, record):
        if self.last_dollar == record['$']:
            if record['$'] == 'before':
                self.level += 1
            else:
                self.level -= 1
        self.last_dollar = record['$']
        if record['$'] == 'before':
            return ' '.join(['\t' * self.level, record['payload'].get('text', '').format(**record['payload'])])
    
    def __call__(self, record: Dict[str, Any]):
        s = self.format(record)
        url = self.url
        if url and s:
            self.logfail_count.setdefault(url, 0)
            if self.logfail_count[url] < self.logfail_max:
                try:
                    requests.post(
                        url,
                        s.encode('utf-8'),
                        headers={'Content-type': 'text/plain; charset=utf-8'},
                        timeout=self.timeout,
                    )
                    self.logfail_count[url] = 0
                except requests.exceptions.ConnectTimeout as e:
                    self.logfail_count[url] += 1
                    self.errorlogger.error("Exception during lws log {} of {}: {}".format(self.logfail_count[url],
                                                                                            self.logfail_max, e))
                    if self.logfail_count[url] == self.logfail_max:
                        self.errorlogger.error("Disabling lws log, max retries encountered for url {}".format(url))
                except Exception:
                    pass
            else:
                self.errorlogger.debug("Skipping lws log, max retries encountered for url {}".format(url))


def mix_bottom_top(pip,
                   reps: int,
                   vol: float,
                   pos: Callable[[float], Location],
                   bottom: float,
                   top: float,
                   last_dispense_rate: float = None,
                   last_mix_volume: float = None):
    """Custom mixing procedure aspirating at the bottom and dispensing at the top
    :param pip: The pipette
    :param reps: Number of repeats
    :param vol: Volume to mix
    :param pos: Method for getting the position
    :param bottom: Offset for the bottom position
    :param top: Offset for the top position
    :param last_dispense_rate: Dispense rate for the last transfer to keep the tip clean
    :param last_mix_volume: volume to mix the last time."""

    for i in range(reps):
        mix_vol = vol
        if i+1 == reps:
            if last_dispense_rate is not None:
                pip.flow_rate.dispense = last_dispense_rate
            if last_mix_volume is not None:
                mix_vol = last_mix_volume
        pip.aspirate(mix_vol, pos(bottom))
        pip.dispense(mix_vol, pos(top))


def mix_walk(
    pip,
    reps: int,
    vol: float,
    aspirate_locs: Union[Iterable, Location],
    dispense_locs: Optional[Union[Iterable, Location]] = None,
    speed: Optional[float] = None,
    logger: Optional[logging.getLoggerClass()] = None
):
    """Custom mixing procedure aspirating and dispensing at custom positions
    :param pip: The pipette
    :param reps: Number of repeats
    :param vol: Volume to mix
    :param aspirate_locs: Position(s) at which to aspirate. If less than reps, they are cycled over.
    :param dispense_locs: Position(s) at which to dispense (optional). If less than reps, they are cycled over. If not specified, dispense in place
    :param speed: Speed for moving the pipette around the mixing position (optional). At the end, the previous speed is restored
    :param logger: Logger for debugging information (optional)"""
    if isinstance(aspirate_locs, Location):
        aspirate_locs = [aspirate_locs]
    if dispense_locs is None:
        aspirate_locs, dispense_locs = tee(aspirate_locs, 2)
    elif isinstance(dispense_locs, Location):
        dispense_locs = [dispense_locs]
    
    old_speed = pip.default_speed
    
    for b, a, d in islice(zip(chain([True], repeat(False)), cycle(aspirate_locs), cycle(dispense_locs)), reps):
        if b and speed is not None:
            pip.move_to(a)
            pip.default_speed = speed
            if logger is not None:
                logger.debug('set speed to {}'.format(speed))
        if logger is not None:
            logger.debug('mixing at {} and {}'.format(a, d))
        pip.aspirate(vol, a)
        pip.dispense(vol, d)
    
    if logger is not None and speed is not None:
        logger.debug('set speed to {}'.format(old_speed))
    pip.default_speed = old_speed


def uniform_divide(total: float, mpp: float) -> Tuple[int, float]:
    """Return the minimum number of partitions and the quantity per partition that uniformly divide a given quantity
    :param total: The total quantity to divide
    :param mpp: Maximum quantity per partition
    :returns: The minimum number of partitions and the quantity in each partition"""
    n = int(math.ceil(total / mpp))
    p = total / n if n else 0
    return n, p


class WellWithVolume:
    """Class to make easy to calcualate and use the height of the liquid in a well"""
    def __init__(self, well: Well, initial_vol: float, min_height: float = 0.5, headroom_height: float = 2.0):
        """Class initialization
        :param total_vol: the total volume expected in the well
        :param min_height: optional, the minimum height
        :param headroom_height: optional, the height in mm of liquid above the tip expected after the aspirate
        """
        self._well = well

        assert initial_vol >= 0, "WellWithVolume initial volume negative for well {}".format(well)
        self._volume = initial_vol

        self._min_height = min_height
        self._headroom_height = headroom_height

    @property
    def height(self) -> float:
        if self._well.diameter:
            remaining_height = self._volume / (math.pi * (self._well.diameter/2)**2)
        else:
            remaining_height = self._volume / self._well.length**2

        remaining_height -= self._headroom_height
        final_height = max(remaining_height, self._min_height)
        return final_height

    def extract_vol_and_get_height(self, aspirate_vol: float) -> float:
        """Return the maximum height to aspirate safely a volume from a well
        :param aspirate_vol: The volume to aspirate
        :returns: the maximum height to aspirate safely the volume in the well"""
        self._volume = self._volume - aspirate_vol if self._volume > aspirate_vol else 0

        return self.height

    def fill(self, vol: float):
        """Add the volume passed to the well"""

        self._volume = self._volume + vol
        if self._volume < 0:
            self._volume = 0


class MoveWithSpeed:
    """Class to make easy aspirate and dispense approaching with a defined speed.
    This should be useful with viscous liquid in order not to break the external meniscus on tip avoiding drops"""
    def __init__(self, pip: Union[InstrumentContext, PairedInstrumentContext],
                 from_point: Location,
                 to_point: Location,
                 speed,
                 move_close: bool = True,
                 go_away: bool = True,
                 logger: logging.Logger = logging.getLogger("MovieWithSpeed")):
        """Class initialization
        :param pip: pipette to move;
        :param from_point: first point to reach at default speed and last point to leave;
        :param to_point: target point; from from_point to this point the speed parameter is used;
        :param speed: speed for the movement between from_point and to_point and back
        :param move_close: speed is set going towards to_point
        :param go_away: speed is set going back to from_point."""
        self._move_close = move_close
        self._go_away = go_away
        self._pip = pip
        self._from_point = from_point
        self._to_point = to_point
        self._speed = speed
        self._logger = logger

        # We want to force_direct only if from and to point are on the same well.
        if self._to_point.labware.is_well and self._from_point.labware.is_well:
            self._logger.debug("Both labware are well")
            self._force_direct = self._to_point.labware.as_well() == self._from_point.labware.as_well()
        else:
            self._logger.debug("One labware is not well {}, {}".format(self._from_point.labware, self._to_point.labware))
            self._force_direct = False
        self._logger.debug("Force direct is: {}".format(self._force_direct))

    def __enter__(self):
        self._logger.debug("Moving close. Force direct is: {}".format(self._force_direct))
        if self._move_close:
            self._pip.move_to(self._from_point)
            self._pip.move_to(self._to_point, force_direct=self._force_direct, speed=self._speed)
        else:
            self._pip.move_to(self._to_point)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger.debug("Moving close. Force direct is: {}".format(self._force_direct))
        self._pip.move_to(self._to_point)       # for safety, since we've a force_direct set on next move_to
        self._pip.move_to(self._from_point, force_direct=self._force_direct, speed=self._speed if self._go_away else None)


def get_labware_json_from_filename(filename: str = ""):
    with open(os.path.join(os.path.dirname(__file__), 'labware', filename)) as f:
        return json.load(f)


class DelayManager:
    def __init__(self,
                 logger: logging.Logger = logging.getLogger("DelayManager")):
        self._logger = logger
        self._start_time = 0
        self._duration = 0

    def start(self):
        self._start_time = time.time()
        self._duration = 0
        self._logger.info("Entering; now is {}".format(time.strftime("%H:%M", time.localtime(self._start_time))))

    def stop(self):
        self._duration = (time.time() - self._start_time) / 60
        self._logger.info("Exiting; actual duration is {:.2f} minutes".format(self._duration))

    def get_remaining_delay(self, seconds: float = 0, minutes: float = 0) -> float:
        total_time_minutes = seconds/60 + minutes
        delay = (total_time_minutes - self._duration) if total_time_minutes > self._duration else 0
        self._logger.info("Returning delay of {:.2f} minutes".format(delay))
        return delay

    @property
    def start_time(self):
        return self._start_time

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
