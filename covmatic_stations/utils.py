from opentrons.protocol_api import ProtocolContext
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
    def __init__(self, ip: Optional[str] = None, endpoint: str = ":5002/log", timeout: float = 2, *args, **kwargs):
        super(LocalWebServerLogger, self).__init__(*args, **kwargs)
        self.ip = ip
        self.endpoint = endpoint
        self.timeout = timeout
        self.level = 0
        self.last_dollar = None
    
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
            try:
                requests.post(
                    url,
                    s.encode('utf-8'),
                    headers={'Content-type': 'text/plain; charset=utf-8'},
                    timeout=self.timeout,
                )
            except Exception:
                pass


def mix_bottom_top(pip, reps: int, vol: float, pos: Callable[[float], Location], bottom: float, top: float):
    """Custom mixing procedure aspirating at the bottom and dispensing at the top
    :param pip: The pipette
    :param reps: Number of repeats
    :param vol: Volume to mix
    :param pos: Method for getting the position
    :param bottom: Offset for the bottom position
    :param top: Offset for the top position"""
    for _ in range(reps):
        pip.aspirate(vol, pos(bottom))
        pip.dispense(vol, pos(top))


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
    p = total / n
    return n, p


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
