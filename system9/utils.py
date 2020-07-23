from opentrons.protocol_api import ProtocolContext
import logging
import math
from typing import Tuple


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


def mix_bottom_top(pip, reps: int, vol: float, pos, bottom: float, top: float):
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


def uniform_divide(total: float, mpp: float) -> Tuple[int, float]:
    """Return the minimum number of partitions and the quantity per partition that uniformly divide a given quantity
    :param total: The total quantity to divide
    :param mpp: Maximum quantity per partition
    :returns: The minimum number of partitions and the quantity in each partition"""
    n = int(math.ceil(total / mpp))
    p = total / n
    return n, p
