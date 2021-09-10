from opentrons.types import Mount, Point
from opentrons.hardware_control import CriticalPoint


class HardwareHelper:
    def __init__(self, ctx):
        self._ctx = ctx

    def get_gantry_position(self, m: Mount, update_position: bool = False) -> Point:
        return self._ctx._hw_manager.hardware.gantry_position(m, CriticalPoint.MOUNT, update_position)

    def move_rel(self, mount, delta: Point):
        return self._ctx._hw_manager.hardware.move_rel(mount, delta)

    def retract(self, mount):
        self._ctx._hw_manager.hardware.retract(mount)
