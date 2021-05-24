# -------------------------------------------------------------------------
from opentrons.protocols.api_support.util import labware_column_shift
from opentrons.protocol_api.paired_instrument_context import PairedInstrumentContext, PipettePairPickUpTipError
from opentrons.protocol_api.labware import Well
from opentrons import types
import logging
import parse


class PairedPipette:
    available_commands = ["pick_up", "drop_tip", "mix", "air_gap", "aspirate", "dispense", "move_to"]
    pips = []
    pippairedctx = None

    @classmethod
    def setup(cls, pipette1, pipette2, stationctx):
        cls.pips = [pipette1, pipette2]
        cls.pippairedctx = pipette1.pair_with(pipette2)
        cls._stationctx = stationctx

    def __init__(self, labware, targets, **kwargs):
        # dests è un iterabile che contiene le destinazioni
        self.labware = labware
        self.donedests = []
        self.switchpipette = 1  ## used to switch between pipettes when single pipette is requested
        self.commands = []
        self._logger = logging.getLogger(__name__)
        self._locations = {'target': targets}
        self._locations_as_well = [self._get_well_from_location(location) for location in self._locations['target']]
        for kwarg in kwargs:
            self._logger.debug("Appending {} to keywork {}".format(kwargs[kwarg], kwarg))
            self._locations[kwarg] = kwargs[kwarg]
        self._logger.debug("Locations now contain: {}".format(self._locations))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._run()

    def getctx(self, dest_well):
        assert self.__class__.pips, "You must initialize the module with setup first"
        try:
            secondary_well = labware_column_shift(dest_well, self.labware)
            if secondary_well in self._locations_as_well and secondary_well not in self.donedests:
                self._logger.debug("We can use paired pipette on destination.")
                return self.__class__.pippairedctx, secondary_well
        except IndexError:
            self._logger.debug("We can't use paired pipette here.")
        return self._get_single_pipette(), None

    def _get_single_pipette(self):
        self.switchpipette = (self.switchpipette + 1) % len(self.__class__.pips)
        return self.__class__.pips[self.switchpipette]

    def _pick_up_tip(self, pipctx):
        self._logger.debug("Trying to pick up a tip")
        try:
            self._stationctx.pick_up(pipctx)
        except PipettePairPickUpTipError:
            self._logger.debug("Paired pipette needed but cannot pickup tips, doing one pipette at a time")
            for p in self.pips:
                self._stationctx.pick_up(p)

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
        if 'location' in kwargs:
            assert isinstance(kwargs['location'], str), "location parameter must be a string."
            if kwargs['location'] in self._locations:
                loc_keyword = kwargs.pop('location')
                kwargs['location'] = self._locations[loc_keyword][index]
            else:
                raise Exception("Location {} not set.".format(kwargs['location']))

    def substitute_kwargs_well_modifier(self, kwargs):
        if 'well_modifier' in kwargs:
            if 'location' in kwargs:
                call, arguments = parse.parse("{}({})", kwargs['well_modifier'])
                # arguments conversion to string
                if call in ['top', 'bottom']:
                    arguments = float(arguments)
                kwargs.pop('well_modifier')
                old_location = kwargs.pop('location')
                kwargs['location'] = getattr(old_location, call)(arguments)

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
            self._execute_command_list_on(d, d_well)

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
                else:
                    substituted_kwargs = dict(c['kwargs'])  # copy kwargs and substitute time by time
                    # substituting kwargs to represent actual data
                    self.substitute_kwargs_locations(primary_well_index, substituted_kwargs)
                    self.substitute_kwargs_well_modifier(substituted_kwargs)

                    if isinstance(pipctx, PairedInstrumentContext) \
                            and substituted_kwargs.get('location', None) \
                            and self._get_well_from_location(
                        substituted_kwargs['location']) not in self.labware.wells():
                        self._logger.debug("We aren't on the destination plate... so we use single pipetting")
                        substituted_kwargs_pip2 = dict(c['kwargs'])
                        self.substitute_kwargs_locations(secondary_well_index, substituted_kwargs_pip2)
                        self.substitute_kwargs_well_modifier(substituted_kwargs_pip2)

                        for (p, kwargs) in zip(self.__class__.pips, [substituted_kwargs, substituted_kwargs_pip2]):
                            self._logger.debug("Pipette {} command: {} args: {} {}".format(p, c['command'], c['args'], kwargs))
                            getattr(p, c['command'])(*c['args'], **kwargs)
                            # Merging air_gap with preceeding command
                            if len(self.commands) > (j + 1) and self.commands[j + 1]['command'] == 'air_gap':
                                self._logger.debug("Doing air_gap on {}".format(p))
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
        self.setcommand('air_gap', *args, **kwargs)

    def mix(self, *args, **kwargs):
        if 'location' not in kwargs:
            kwargs['location'] = 'target'
        self.setcommand('mix', *args, **kwargs)

    def aspirate(self, *args, **kwargs):
        self.setcommand('aspirate', *args, **kwargs)

    def dispense(self, *args, **kwargs):
        self.setcommand('dispense', *args, **kwargs)

    def move_to(self, *args, **kwargs):
        self.setcommand('move_to', *args, **kwargs)
