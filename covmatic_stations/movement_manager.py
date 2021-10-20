from .hardware import HardwareHelper
from opentrons.types import Mount, Point
from opentrons.hardware_control.types import PipettePair

import logging

class MovementManager:
    def __init__(self, ctx, logger=logging.getLogger(__name__)):
        self._ctx = ctx
        self._hw_helper = HardwareHelper(ctx)
        self._home_pos: dict = {}
        self._logger = logger

    def move_to_home(self, safety_margin=10, force: bool = False):
        ''' Move pipettes near home
            without really homing to save time since homing is not needed
            :param safety_margin: the distance to keep from home position (not to hit the home switches)
            :param force: force the movement without checking if the gantry is near home
        '''
        self._ctx.comment("Moving near home")
        if Mount.LEFT not in self._home_pos or Mount.RIGHT not in self._home_pos:
            self._ctx.home()
            self.save_home_pos_if_needed()
        else:
            actual_pos = dict()
            for m in [Mount.LEFT, Mount.RIGHT]:
                actual_pos[m] = self._hw_helper.get_gantry_position(m)
                self._logger.debug("Got ActualPos {} for mount {}".format(actual_pos[m], m))
                if actual_pos[m].z != self._home_pos[m].z:
                    self._logger.debug("Retracting {}".format(m))
                    self.retract()
                else:
                    self._logger.debug("Not retracting {}".format(m))

            self._logger.debug("actual pos L: {}".format(actual_pos[Mount.LEFT]))
            self._logger.debug("actual pos R: {}".format(actual_pos[Mount.RIGHT]))
            self._logger.debug("required pos L: {}".format(self._home_pos[Mount.LEFT]))
            self._logger.debug("required pos R: {}".format(self._home_pos[Mount.RIGHT]))

            if force or self._need_home(actual_pos, safety_margin):
                target_mount = Mount.RIGHT if self._mount is Mount.RIGHT else Mount.LEFT     # avoiding PairedPipette Mounts
                target_pos = self._home_pos[target_mount]
                delta_pos = Point(target_pos.x - actual_pos[target_mount].x - safety_margin,
                                  target_pos.y - actual_pos[target_mount].y - safety_margin, 0)
                self._hw_helper.move_rel(target_mount, delta_pos)

    def home(self):
        self._ctx.home()
        self.save_home_pos_if_needed()

    def save_home_pos_if_needed(self):
        ''' saves the home position for the first time
            ==>> WARNING: To be called right AFTER a home command <<==
        '''
        for m in [Mount.LEFT, Mount.RIGHT]:
            self._logger.debug("Saving mount {}".format(m))
            if self._home_pos.get(m, None) is None:
                self._home_pos[m] = self._hw_helper.get_gantry_position(m, True)

    def retract(self):
        ''' We try to retract the pipette attached
            if we have zero or two pipette retract both two axes.'''
        self._logger.debug("Retracting mount {}".format(self._mount))
        self._hw_helper.retract(self._mount)

    @property
    def _mount(self):
        ''' Get the actual mount to use for pseudo-homing
            if only one pipette is present that mount is taken, otherwise the left one '''
        if len(self._ctx.loaded_instruments) == 1:
            mount = Mount.LEFT if 'left' in self._ctx.loaded_instruments else Mount.RIGHT
        else:
            mount = PipettePair.PRIMARY_LEFT
        self._logger.debug("Returning mount {}".format(mount))
        return mount

    def _need_home(self, actual_positions, safety_margin: float) -> bool:
        x_is_near_home = False
        y_is_near_home = False

        for m in [Mount.LEFT, Mount.RIGHT]:
            if m in actual_positions:
                self._logger.debug("Mount {}, Actual x: {}, trash x: {}".format(m, actual_positions[m].x, self._ctx.fixed_trash['A1'].center().point.x))
                self._logger.debug("Mount {}, Actual y: {}, trash y: {}".format(m, actual_positions[m].y,
                                                                               self._ctx.fixed_trash[
                                                                                   'A1'].center().point.y))
                x_is_near_home = x_is_near_home or \
                            actual_positions[m].x + safety_margin >= self._ctx.fixed_trash['A1'].center().point.x or \
                            actual_positions[m].x + safety_margin == self._home_pos[m].x
                y_is_near_home = y_is_near_home or \
                            actual_positions[m].y + safety_margin >= self._ctx.fixed_trash['A1'].center().point.y or \
                            actual_positions[m].y + safety_margin == self._home_pos[m].y
        self._logger.debug("X near: {}, Y near: {}".format(x_is_near_home, y_is_near_home))
        return not (x_is_near_home and y_is_near_home)

