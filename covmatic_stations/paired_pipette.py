# -------------------------------------------------------------------------
from opentrons.protocols.api_support.util import labware_column_shift
from opentrons.protocol_api.paired_instrument_context import PairedInstrumentContext, PipettePairPickUpTipError
from opentrons.protocol_api.labware import Well, Labware
from opentrons import types
import logging
import parse
from opentrons.types import Mount, Point, Location


class PairedPipette:
    available_commands = ["pick_up", "drop_tip", "mix", "air_gap", "aspirate", "dispense", "move_to", "touch_tip", "comment"]
    pips = []
    pippairedctx = None
    labware_height_overhead = 10.0      # mm height over the top of the tallest labware

    @classmethod
    def setup(cls, pipette1, pipette2, stationctx):
        cls.pips = [pipette1, pipette2]
        cls.pippairedctx = pipette1.pair_with(pipette2)
        cls._stationctx = stationctx
        cls.max_labware_height = cls.labware_height_overhead + \
            max([labware.highest_z for labware in cls._stationctx._ctx.loaded_labwares.values()])

    def __init__(self, labware, targets, start_at:str = None, **kwargs):
        # dests è un iterabile che contiene le destinazioni
        assert isinstance(labware, Labware), "Paired pipette labware not a labware but a {}".format(type(labware))
        self.labware = labware
        self.donedests = []
        self.switchpipette = 1  ## used to switch between pipettes when single pipette is requested
        self.commands = []
        self._logger = logging.getLogger(PairedPipette.__name__)
        self._logger.setLevel(logging.INFO)
        self._locations = {'target': targets}
        self._locations_as_well = [self._get_well_from_location(location) for location in self._locations['target']]
        for kwarg in kwargs:
            self._logger.debug("Appending {} to keywork {}".format(kwargs[kwarg], kwarg))
            self._locations[kwarg] = kwargs[kwarg]
        self._logger.debug("Locations now contain: {}".format(self._locations))
        self._start_at = start_at
        if self._start_at:
            assert callable(getattr(self._stationctx, "run_stage")), \
                "run_stage function not found. Please do not use start_at names."
            self._start_at_function = getattr(self._stationctx, "run_stage")
            self._start_at += " {}/{}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._run()

    def getctx(self, dest_well):
        assert self.__class__.pips, "You must initialize the module with setup first"
        try:
            _, secondary_well = self.pippairedctx._get_locations(dest_well)
            self._logger.debug("Primary well: {}. Secondary well found: {}".format(dest_well, secondary_well))
            if secondary_well in self._locations_as_well and secondary_well not in self.donedests:
                self._logger.debug("We can use paired pipette on destination.")
                return self.__class__.pippairedctx, secondary_well
        except PipettePairPickUpTipError as e:
            self._logger.debug("We can't use paired pipette here. Exception: {}".format(e))
        pipette_to_use = self._get_single_pipette()
        self._check_pipette_over_labware(self.__class__._get_other_pipette(pipette_to_use))
        return pipette_to_use, None

    def _get_single_pipette(self):
        """ Get a single pipette to use for a single-pipette operation"""
        # self.switchpipette = (self.switchpipette + 1) % len(self.__class__.pips)
        # return self.__class__.pips[self.switchpipette]
        # for now use only one pipette if single pipette needed.
        # TODO maybe switch pipette each run?
        return self.__class__.pips[0]

    def _pick_up_tip(self, pipctx):
        self._logger.debug("Trying to pick up a tip")
        try:
            self._stationctx.pick_up(pipctx)
        except PipettePairPickUpTipError:
            self._logger.debug("Paired pipette needed but cannot pickup tips, doing one pipette at a time")
            for p in self.pips:
                self._stationctx.pick_up(p)

    def _drop_tip(self, pipctx):
        try:
            self._stationctx.drop(pipctx)
        except TypeError:
            if isinstance(pipctx, PairedInstrumentContext):
                self._logger.debug("Pip ctx {}: probably pick_up_tip has been done with single pipette".format(pipctx))
                self._check_pipette_over_labware(pipctx)    # before move single pipette bring each pipette in safe position
                for p in self.pips:
                    self._stationctx.drop(p)

    def _check_pipette_over_labware(self, pipctx):
        """Check that the pipette has enough height to pass over all labware"""
        mount = pipctx._pair_policy.primary if isinstance(pipctx,
                                                          PairedInstrumentContext) else pipctx._implementation.get_mount()
        current_loc = self._stationctx._ctx._hw_manager.hardware.gantry_position(mount)
        self._logger.debug("{}: Actual location for mount {} is: {}".format(pipctx, mount, current_loc))
        if current_loc.z < self.__class__.max_labware_height:
            new_point = Point(x=current_loc.x, y=current_loc.y, z=self.__class__.max_labware_height)
            self._logger.debug("Location to move to: {}".format(new_point))
            pipctx.move_to(Location(new_point, None))

    @staticmethod
    def substitute_kwarg_location(new_location, keyword, kwargs):
        if keyword in kwargs:
            call, arguments = parse.parse("{}({})", kwargs[keyword])
            # arguments conversion to string
            if call in ['top', 'bottom']:
                arguments = float(arguments)

            kwargs.pop(keyword)
            kwargs['location'] = getattr(new_location, call)(arguments)

    def substitute_kwargs_locations(self, index, kwargs):
        if 'locationFrom' in kwargs:
            assert isinstance(kwargs['locationFrom'], str), "location parameter must be a string."
            if kwargs['locationFrom'] in self._locations:
                loc_keyword = kwargs.pop('locationFrom')
                assert 'location' not in kwargs, "location already set, not overwriting. Value: {}".format(kwargs['location'])
                kwargs['location'] = self._locations[loc_keyword][index]
            else:
                raise Exception("Location {} not set.".format(kwargs['locationFrom']))

    def substitute_kwargs_well_modifier(self, kwargs):
        if 'well_modifier' in kwargs:
            if 'location' in kwargs:
                self._logger.debug("Substitute kwargs {}".format(kwargs['location']))
                call, arguments = parse.parse("{}({})", kwargs['well_modifier'])
                # arguments conversion to string
                if call in ['top', 'bottom']:
                    arguments = float(arguments)
                kwargs.pop('well_modifier')
                old_location = kwargs.pop('location')
                kwargs['location'] = getattr(old_location, call)(arguments)
    @classmethod
    def _get_other_pipette(cls, pip):
        for p in cls.pips:
            if p != pip:
                return p
        raise Exception("Different pipette not found")

    @staticmethod
    def _get_well_from_location(loc) -> Well:
        if loc and isinstance(loc, types.Location):
            if loc.labware.is_well:
                well = loc.labware.as_well()
            else:
                raise Exception("Cannot make Well from destination {} of type {}.".format(loc, type(loc)))
        elif loc and isinstance(loc, Well):
            well = loc
        else:
            raise Exception("Destination {} of type {} not recognized.".format(loc, type(loc)))
        return well

    def _run(self):
        for i, (d, d_well) in enumerate(zip(self._locations['target'], self._locations_as_well)):
            self._logger.debug("Well is: {}".format(d_well))
            if self._start_at and self._start_at_function(self._start_at.format(i+1, len(self._locations['target']))):
                self._execute_command_list_on(d, d_well)

    @staticmethod
    def _getValueFromKwargsAndClean(kwargs, key: str, default_value):
        if key in kwargs:
            ret_value = kwargs.pop(key)
        else:
            ret_value = default_value
        return ret_value

    def _execute_command_list_on(self, location, well):
        if well not in self.donedests:
            pipctx, secondary_well = self.getctx(well)
            primary_well_index = self._locations_as_well.index(well)
            secondary_well_index = self._locations_as_well.index(secondary_well) if secondary_well else None
            self._logger.debug("Using pipette context: {}".format(pipctx))
            skip_next_command = False       # skip_next_command is for merging aspirate and air-gap on each pipette
            for j, c in enumerate(self.commands):
                self._logger.debug("Evaluating command: {}".format(c))
                if skip_next_command:
                    self._logger.debug("Asked to skip command.")
                    skip_next_command = False
                    continue

                if c['command'] == "pick_up":
                    self._pick_up_tip(pipctx)
                elif c['command'] == "drop_tip":
                    self._drop_tip(pipctx)
                elif c['command'] == "comment":
                    self._stationctx._ctx.comment(*c['args'], **c['kwargs'])
                else:
                    substituted_kwargs = dict(c['kwargs'])  # copy kwargs and substitute time by time
                    # substituting kwargs to represent actual data
                    is_target_paired = 'locationFrom' in substituted_kwargs
                    is_forced_single = self._getValueFromKwargsAndClean(substituted_kwargs, 'forceSingle', False)
                    is_command_ok_with_paired = self._getValueFromKwargsAndClean(substituted_kwargs, 'isOkWithPaired', False)
                    self._logger.debug("Target is paired: {}; forced single: {}; command ok with paired: {}"
                                       .format(is_target_paired, is_forced_single, is_command_ok_with_paired))
                    self.substitute_kwargs_locations(primary_well_index, substituted_kwargs)
                    self.substitute_kwargs_well_modifier(substituted_kwargs)

                    to_do_with_single =  (is_target_paired==False and is_command_ok_with_paired==False) or is_forced_single
                    self._logger.debug("To do with single is: {}".format(to_do_with_single))

                    if isinstance(pipctx, PairedInstrumentContext) and to_do_with_single:
                        self._logger.debug("Using single pipetting")
                        substituted_kwargs_pip2 = dict(c['kwargs'])
                        self._getValueFromKwargsAndClean(substituted_kwargs_pip2, 'forceSingle', False)
                        self._getValueFromKwargsAndClean(substituted_kwargs_pip2, 'isOkWithPaired', False)
                        self.substitute_kwargs_locations(secondary_well_index, substituted_kwargs_pip2)
                        self.substitute_kwargs_well_modifier(substituted_kwargs_pip2)

                        for (p, kwargs) in zip(self.__class__.pips, [substituted_kwargs, substituted_kwargs_pip2]):
                            self._logger.debug("Pipette {} command: {} args: {} {}".format(p, c['command'], c['args'], kwargs))
                            self._check_pipette_over_labware(self.__class__._get_other_pipette(p))
                            getattr(p, c['command'])(*c['args'], **kwargs)
                            # Merging air_gap with preceeding command
                            if len(self.commands) > (j + 1) and self.commands[j + 1]['command'] == 'air_gap':
                                self._logger.debug("Doing air_gap on {}".format(p))
                                self._getValueFromKwargsAndClean(self.commands[j + 1]['kwargs'], 'forceSingle', False)
                                self._getValueFromKwargsAndClean(self.commands[j + 1]['kwargs'], 'isOkWithPaired', False)
                                getattr(p, 'air_gap')(*self.commands[j + 1]['args'],
                                                      **self.commands[j + 1]['kwargs'])
                                skip_next_command = True
                    else:
                        self._logger.debug("Pipette {} command: {} args: {} {}".format(pipctx, c['command'], c['args'],
                                                                          substituted_kwargs))
                        getattr(pipctx, c['command'])(*c['args'], **substituted_kwargs)
            self.donedests.append(well)
            if secondary_well is not None:
                self.donedests.append(secondary_well)
            self._logger.debug("donedests contains: {}".format(self.donedests))
        else:
            self._logger.debug("dest {} skipped, already done.".format(well))

    def setcommand(self, command, *args, **kwargs):
        assert command in self.available_commands, "Command {} not recognized.".format(command)
        self.commands.append({'command': command, 'args': list(args), 'kwargs': kwargs})

    # API
    # as a real pipette apart from "source" and "dest" location keyword
    #
    # keep in mind that can be used only ine location at a time (eg. no transfer from source to dest):
    # - source keywork (eg. source="bottom(1)") will be replaced with location=s.bottom(1)
    # - dest keywork (eg. dest="top(-2)") will be replaced with location=d.top(-2)

    def pick_up(self):
        self.setcommand('pick_up')

    def drop_tip(self):
        self.setcommand('drop_tip')

    def air_gap(self, *args, **kwargs):
        kwargs['isOkWithPaired'] = True
        self.setcommand('air_gap', *args, **kwargs)

    def mix(self, *args, **kwargs):
        self.setcommand('mix', *args, **kwargs)

    def aspirate(self, *args, **kwargs):
        self.setcommand('aspirate', *args, **kwargs)

    def dispense(self, *args, **kwargs):
        self.setcommand('dispense', *args, **kwargs)

    def move_to(self, *args, **kwargs):
        self.setcommand('move_to', *args, **kwargs)

    def touch_tip(self, *args, **kwargs):
        kwargs['isOkWithPaired'] = True
        self.setcommand('touch_tip', *args, **kwargs)

    def comment(self, *args, **kwargs):
        self.setcommand('comment', *args, **kwargs)