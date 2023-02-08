import sys
from json import JSONDecodeError
from threading import Timer

from . import __version__, __file__ as module_path

from .movement_manager import MovementManager
from .request import StationRESTServerThread, DEFAULT_REST_KWARGS
from .sound_manager import SoundManager
from .utils import ProtocolContextLoggingHandler, LocalWebServerLogger, DelayManager
from .lights import Button, BlinkingLightHTTP, BlinkingLight
from opentrons.protocol_api import ProtocolContext
from opentrons.protocol_api.paired_instrument_context import PairedInstrumentContext
from opentrons.types import Point
import opentrons.commands.types
from abc import ABCMeta, abstractmethod
from functools import wraps, partialmethod
from itertools import chain, dropwhile
from opentrons.types import Location
from typing import Optional, Callable, Tuple
import json
import math
import os
import logging
import time
import signal


def loader(key):
    def loader_(idx: int = 0, *items: tuple) -> Callable:
        def _labware_loader(method: Callable) -> Callable:
            @wraps(method)
            def method_(self, *args, **kwargs):
                if items:
                    self.logger.debug("loading {}".format(", ".join(map(str, items))))
                return method(self, *args, **kwargs)
            
            setattr(method_, key, (idx, items))
            return method_
        return _labware_loader
    return loader_


# Decorator for labware loader methods
labware_loader = loader("_labware_load")
# Decorator for instrument loader methods
instrument_loader = loader("_instr_load")


def wells(rack):
    return rack.wells()


def first_row(rack):
    return rack.rows()[0]


class StationMeta(ABCMeta):
    def __new__(meta, name, bases, classdict):
        logger = logging.getLogger()
        c = super(StationMeta, meta).__new__(meta, name, bases, classdict)
        logger.info("Class {} looking for messages".format(name))
        try:
            msg_file = os.path.join(os.path.dirname(sys.modules[c.__module__].__file__), 'msg', '{}.json'.format(name))
            logger.debug("Opening file {}".format(msg_file))
            with open(msg_file) as f:
                c._messages = json.load(f)
        except FileNotFoundError:
            logger.warning("No msg file found for class {}".format(name))
            c._messages = {}
        except AttributeError as e:
            logger.error("Unexpected error loading msg file: {}".format(e))
            c._messages = {}
        return c
    
    def get_message(cls, key: str, lan: str = 'ENG'):
        for c in cls.__mro__:
            d = getattr(c, '_messages', {})
            if key in d:
                d = d[key]
                if lan in d:
                    return d[lan]
        return key


class Station(metaclass=StationMeta):
    _protocol_description = "[BRIEFLY DESCRIBE YOUR PROTOCOL]"
    
    def __init__(self,
        debug_mode = False,
        drop_height: float = -2,
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_loc_y: float = 0,
        drop_threshold: int = 296,
        dummy_lights: bool = True,
        jupyter: bool = True,
        log_filepath: Optional[str] = '/var/lib/jupyter/notebooks/outputs/run_{}.log',
        log_file_format: Optional[str] = '%(asctime)s %(levelname)s %(message)s',
        log_file_date_format: Optional[str] = '%Y-%m-%d %H:%M:%S',
        log_lws_enable: Optional[str] = True,
        log_lws_ip: Optional[str] = None,
        log_lws_endpoint: str = ":5002/log",
        logger: Optional[logging.getLoggerClass()] = None,
        language: str = "ENG",
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        protocol_exception_filepath: Optional[str] = '/var/lib/jupyter/notebooks/outputs/error_{}.log',
        rest_server_kwargs: dict = DEFAULT_REST_KWARGS,
        samples_per_col: int = 8,
        skip_delay: bool = False,
        start_at: Optional[str] = None,
        simulation_log_file: bool = False,
        simulation_log_lws: bool = False,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = '/var/lib/jupyter/notebooks/outputs',
        tip_track: bool = True,
        wait_first_log: bool = False,
        watchdog_enable: bool = False,
        watchdog_timeout: int = 180,   # timeout in seconds
        **kwargs,
    ):
        self._debug_mode = debug_mode
        self._delay_manager = DelayManager()
        self._drop_height = drop_height
        self._drop_loc_l = drop_loc_l
        self._drop_loc_r = drop_loc_r
        self._drop_loc_y = drop_loc_y
        self._drop_threshold = drop_threshold
        self._dummy_lights = dummy_lights
        self.jupyter = jupyter
        self.dashboard_input_request = False
        self._language = language
        self._log_filepath = log_filepath.format(time.strftime("%Y_%m_%d__%H_%M_%S"))
        self._log_file_format = log_file_format
        self._log_file_date_format = log_file_date_format
        self._log_lws_enable = log_lws_enable
        self._log_lws_ip = log_lws_ip
        self._log_lws_endpoint = log_lws_endpoint
        self._logger = logger
        self.metadata = metadata
        self._mov_manager = None
        self._num_samples = num_samples
        self._protocol_exception_filepath = protocol_exception_filepath.format(time.strftime("%Y_%m_%d__%H_%M_%S"))
        self._rest_server_kwargs = rest_server_kwargs
        self._samples_per_col = samples_per_col
        self._start_at = start_at
        self._skip_delay = skip_delay
        self._tip_log_filename = tip_log_filename
        self._tip_log_folder_path = tip_log_folder_path
        self._tip_track = tip_track
        self._ctx: Optional[ProtocolContext] = None
        self._drop_count = 0
        self._side_switch = True
        self._simulation_log_file = simulation_log_file
        self._simulation_log_lws = simulation_log_lws
        self._wait_first_log = wait_first_log
        self._waiting_first_log = False
        self._watchdog_enable = watchdog_enable
        self._watchdog_timeout = watchdog_timeout
        self._watchdog = WatchDog(self.log_timeout_exception_and_kill_if_running)
        self.status = "initializing"
        self.stage = None
        self._msg = ""
        self.external = False
        self._run_stage = self._start_at is None
        self._sound_manager = SoundManager() if self._debug_mode else SoundManager(
                                    alarm=os.path.join(os.path.dirname(module_path), 'sounds', 'alarm.mp3'),
                                    beep=os.path.join(os.path.dirname(module_path), 'sounds', 'beep2.mp3'),
                                    finish=os.path.join(os.path.dirname(module_path), 'sounds', 'finish.mp3'))

    def set_external(self, value: bool = True) -> bool:
        self.external = value
        return self.external
    
    set_internal = partialmethod(set_external, value=False)

    def set_dashboard_input(self, value: bool = True) -> bool:
        self.dashboard_input_request = value
        return self.dashboard_input_request
    
    def get_msg(self, value: str) -> str:
        return str(type(self).get_message(value, self._language))
    
    def get_msg_format(self, value: str, *args, **kwargs) -> str:
        return self.get_msg(value).format(*args, **kwargs)
    
    @property
    def msg(self) -> str:
        return self._msg
    
    @msg.setter
    def msg(self, value: str):
        self._msg = self.get_msg(value)
    
    def msg_format(self, value: str, *args, **kwargs) -> str:
        self._msg = self.get_msg_format(value, *args, **kwargs)
        return self.msg
    
    def run_stage(self, stage: str) -> bool:
        self.stage = stage
        if self._start_at == self.stage:
            self._run_stage = True
        self.logger.info("[{}] Stage: {}".format("x" if self._run_stage else " ", self.stage))
        self.watchdog_reset(self._watchdog_timeout)
        return self._run_stage

    def assert_run_stage_has_been_executed(self):
        ''' If a _start_at_ value was requested, check it at least a corresponding stage was found in protocol.'''
        if not self._run_stage:
            raise Exception("Stage '{}' not found.".format(self._start_at))

    def watchdog_reset(self, timeout_seconds):
        if self._watchdog_enable and not self._ctx.is_simulating():
            self._watchdog.reset(timeout_seconds)

    def watchdog_stop(self):
        if self._watchdog_enable and not self._ctx.is_simulating():
            self._watchdog.stop()

    def watchdog_start(self, timeout_seconds):
        if self._watchdog_enable and not self._ctx.is_simulating():
            self._watchdog.start(timeout_seconds)

    @property
    def logger(self) -> logging.getLoggerClass():
        if (not hasattr(self, "_logger")) or self._logger is None:
            self._logger = logging.getLogger(self.logger_name)
        return self._logger

    def setup_protocolcontext_logger(self):
        if self._ctx is not None:
            if self.logger.hasHandlers():
                self.logger.handlers = []
            self.logger.addHandler(ProtocolContextLoggingHandler(self._ctx))

    def setup_opentrons_logger(self):
        stack_logger = logging.getLogger('opentrons')
        stack_logger.setLevel(self.logger.getEffectiveLevel())
        if self._log_filepath and (self._simulation_log_file or not self._ctx.is_simulating()):
            os.makedirs(os.path.dirname(self._log_filepath), exist_ok=True)
            file_handler = logging.FileHandler(self._log_filepath)
            file_handler.setFormatter(logging.Formatter(self._log_file_format, self._log_file_date_format))
            stack_logger.addHandler(file_handler)

        if self._log_lws_enable:
            self._lws_logger = LocalWebServerLogger(self._log_lws_ip, self._log_lws_endpoint)
            if self._simulation_log_lws or not self._ctx.is_simulating():
                self._ctx.broker.subscribe(opentrons.commands.types.COMMAND, self._lws_logger)

    def log_protocol_exception(self, e: Exception):
        with open(self._protocol_exception_filepath, 'w') as f:
            f.write(json.dumps({"error": "{}".format(e)}))

    def log_timeout_exception_and_kill_if_running(self):
        self._logger.error("Stage timeout reached! Killing.")
        self.log_protocol_exception(Exception("Timeout reached"))
        self._sound_manager.play("alarm")
        os.kill(os.getpid(), signal.SIGTERM)

    @property
    def logger_name(self) -> str:
        return self.__class__.__name__
    
    @classmethod
    def loaders(cls, key: str) -> map:
        return map(lambda x: (x[0], x[2]), sorted(map(lambda x: (x, *getattr(getattr(cls, x), key)), filter(lambda x: hasattr(getattr(cls, x), key), dir(cls))), key=lambda x: x[1]))
    
    @classmethod
    def labware_loaders(cls) -> map:
        return cls.loaders("_labware_load")
    
    @classmethod
    def instrument_loaders(cls) -> map:
        return cls.loaders("_instr_load")
    
    def load_it(self, it):
        for method_name, _ in it:
            getattr(self, method_name)()
    
    def load_labware(self):
        self.load_it(self.labware_loaders())
    
    def load_instruments(self):
        self.load_it(self.instrument_loaders())
        
    def equipment(self, it) -> dict:
        return {k: getattr(self, k) for _, v in it for k in v}
    
    @property
    def labware(self) -> dict:
        return self.equipment(self.labware_loaders())
    
    @property
    def instruments(self) -> dict:
        return self.equipment(self.instrument_loaders())
    
    @property
    def num_cols(self) -> int:
        return math.ceil(self._num_samples/self._samples_per_col)
    
    @property
    def _tip_log_filepath(self) -> str:
        return os.path.join(self._tip_log_folder_path, self._tip_log_filename)
    
    @abstractmethod
    def _tipracks(self) -> dict:
        """Mapping from tipracks attribute names to associated pipette (attribute names)"""
        pass

    def _update_tip_log_count(self):
        """Count the number of used tips"""
        self._tip_log['count'] = {t: sum(map(lambda x: not x.has_tip, self._tip_log['tips'][t])) for t in self._tipracks().keys()}

    def _reset_tips(self):
        for key, tiprack in self._tip_log['tips'].items():
            self._reset_tips_in_tiprack(tiprack)

    def _reset_tips_in_tiprack(self, tiprack):
        for t in tiprack:
            t.has_tip = True

    def setup_tip_log(self):
        data_tip_status = {}
        if self._tip_track:
            self.logger.info(self.msg_format("tip info log", self._tip_log_filepath))
            # Checking  with os.stat if the file is empty, so we don't have a JSONDecodeError
            if os.path.isfile(self._tip_log_filepath) and os.stat(self._tip_log_filepath).st_size > 0:
                try:
                    with open(self._tip_log_filepath) as json_file:
                        file = json.load(json_file)
                        data_tip_status: dict = file.get("tip_status", {})
                except JSONDecodeError as e:
                    self.logger.error("Error during tip log read: {}".format(e))
                    raise Exception("Tip log malformed. Please reset it.")
        else:
            self.logger.debug("not using tip log file")
        
        self._tip_log = {
            'tips': {t: list(chain.from_iterable(map(first_row if getattr(self, p).channels > 1 else wells, getattr(self, t)))) for t, p in self._tipracks().items()}
        }
        if data_tip_status:
            for tiprack, tips in data_tip_status.items():
                assert len(tips) == len(self._tip_log['tips'][tiprack]), "Wrong length, please reset tip log"
                for i, tip in enumerate(tips):
                    assert tip.get("name", "") == str(self._tip_log['tips'][tiprack][i]), "Wrong tip order, please reset tip log"
                    self._tip_log['tips'][tiprack][i].has_tip = tip.get("has_tip", False)
        self._tip_log['max'] = {t: len(p) for t, p in self._tip_log['tips'].items()}
        self._update_tip_log_count()
    
    def track_tip(self):
        if self._tip_track and not self._ctx.is_simulating():
            self.logger.debug(self.get_msg_format("tip log dump", self._tip_log_filepath))
            os.makedirs(self._tip_log_folder_path, exist_ok=True)
            with open(self._tip_log_filepath, 'w') as outfile:
                json.dump({
                    "count": self._tip_log['count'],
                    "next": {k: str(self._get_next_tip(v)) for k, v in self._tip_log['tips'].items()},
                    "tip_status": {k: [{'name': str(w), 'has_tip': w.has_tip} for w in self._tip_log['tips'][k]] for k, v in self._tip_log['count'].items()}
                }, outfile, indent=2)

    @staticmethod
    def _get_next_tip(tips):
        available_tips = list(dropwhile(lambda x: not x.has_tip, tips))
        return available_tips[0] if len(available_tips) else None

    def pick_up(self, pip, loc: Optional[Location] = None, tiprack: Optional[str] = None):
        if loc is None:
            if tiprack is None:
                    for t in self._tipracks().keys():
                        if getattr(self, t) == pip.tip_racks:
                            tiprack = t
                            break
            if tiprack is None:
                if isinstance(pip, PairedInstrumentContext):
                    # Paired pipette tiprack doesn't work with the for loop below
                    # pipettes must be the same, so selecting the first tiprack
                    tiprack = list(self._tipracks().keys())[0]
                    self._logger.debug("Selectiong {} tiprack for paired pipette".format(tiprack))
                else:
                    raise RuntimeError("no tiprack associated to pipette {}".format(pip))
            self._update_tip_log_count()
            if self._tip_log['count'][tiprack] == self._tip_log['max'][tiprack]:
                # If empty, wait for refill
                self._reset_tips_in_tiprack(self._tip_log['tips'][tiprack])
                self._update_tip_log_count()
                self.track_tip()
                self.pause(self.get_msg_format("refill tips", "\n".join(map(str, getattr(self, tiprack)))))
            self.track_tip()
            loc = self._get_next_tip(self._tip_log['tips'][tiprack])
        pip.pick_up_tip(loc)
        self._update_tip_log_count()
        self.track_tip()

    @staticmethod
    def _get_pipette_num_channels(pip):
        pips = pip._instruments.values() if isinstance(pip, PairedInstrumentContext) else [pip]
        return sum([p.channels for p in pips])

    def drop(self, pip):
        # Drop in the Fixed Trash (on 12) at different positions to avoid making a tall heap of tips
        drop_loc = self._ctx.loaded_labwares[12].wells()[0].top(self._drop_height).move(Point(x=self._drop_loc_r if self._side_switch else self._drop_loc_l, y=self._drop_loc_y))
        self._side_switch = not self._side_switch
        if self._debug_mode:
            pip.return_tip()
        else:
            pip.drop_tip(drop_loc)
        self._drop_count += self._get_pipette_num_channels(pip)
        if self._drop_count >= self._drop_threshold:
            self.pause('empty tips')
            self._drop_count = 0
    
    def pause(self,
        msg: str = "",
        blink: bool = True,
        blink_period: float = 1,
        color: str = 'red',
        delay_time: float = 0,
        home: bool = True,
        level: int = logging.INFO,
        pause: bool = True,
    ):
        # Note: changed default homing method to 'move_to_home' Agos, 2021-09-13

        old_color = self._button.color
        self._button.color = color

        self.watchdog_stop()

        if msg:
            self.msg = msg
            self.logger.log(level, self.msg)
        if home:
            self.home()
        if blink and not self._ctx.is_simulating():
            self._sound_manager.play("beep")
            lt = (BlinkingLightHTTP if self._dummy_lights else BlinkingLight)(self._ctx, t=blink_period/2)
            lt.start()
        if delay_time > 0:
            self.status = "delay"
            self.watchdog_start(delay_time * 1.2)
            self._ctx.delay(delay_time)
            self.watchdog_stop()
        if pause:
            self.status = "pause"
            self._ctx.pause()
            self._ctx.delay(0.1)  # pad to avoid pause leaking
        if blink and not self._ctx.is_simulating():
            lt.stop()
        self._button.color = old_color
        self.status = "running"
        self.msg = ""



    def dual_pause(self, msg: str, cols: Tuple[str, str] = ('red', 'yellow'), between: Optional[Callable] = None, home: Tuple[bool, bool] = (True, False)):
        msg = self.get_msg(msg)
        self._msg = "{}.\n{}".format(msg, self.get_msg("stop blink"))
        self.pause(self.msg, color=cols[0], home=home[0])
        if between is not None:
            between()
        self._msg = "{}.\n{}".format(msg, self.get_msg("continue"))
        self.pause(self.msg, blink=False, color=cols[1], home=home[1])

    def request_dashboard_input(self, msg: str, home: Tuple[bool, bool] = (True, False)):
        self.logger.info("Requesting external barcode")
        self.dual_pause(msg=msg, home=home, between=self.set_dashboard_input)
        self.set_dashboard_input(False)

    def delay(self,
        mins: float,
        msg: str = "",
        color: str = 'yellow',
        home: bool = True,
        level: int = logging.INFO,
    ):
        self.pause(
            msg=self.get_msg_format("delay minutes", self.get_msg(msg), mins, self.get_msg("skip delay") if self._skip_delay else ""),
            blink=False,
            color=color,
            delay_time=0 if self._skip_delay else (60 * mins),
            home=home,
            level=level,
            pause=self._skip_delay,
        )

    ''' Managed delay
        we start counting, doing something (eg. mixing samples) than we wait for timer to elapse'''
    ''' Start counting function '''
    def delay_start_count(self):
        self._delay_manager.start()

    ''' Delay function '''
    def delay_wait_to_elapse(self, seconds: float = 0, minutes: float = 0):
        self._delay_manager.stop()
        minutes_to_wait = minutes + seconds / 60
        self.delay(self._delay_manager.get_remaining_delay(minutes=minutes_to_wait),
                   self.get_msg_format("waiting delay to elapse", minutes_to_wait))

    def home(self):
        self._mov_manager.move_to_home()

    def body(self):
        pass

    def cleanup(self):
        pass

    def run(self, ctx: ProtocolContext):
        self.status = "running"
        self._ctx = ctx
        self.setup_protocolcontext_logger()
        self._mov_manager = MovementManager(self._ctx)
        self._button = (Button.dummy if self._dummy_lights else Button)(self._ctx, 'blue')
        if self._simulation_log_lws or not self._ctx.is_simulating():
            self._request = StationRESTServerThread(ctx, station=self, **self._rest_server_kwargs)
            self._request.start()

        self.setup_opentrons_logger()
        if self._wait_first_log:
            self._waiting_first_log = True
            self.pause("wait log", blink=False, home=False, color='yellow')
            self._waiting_first_log = False
        
        self.logger.info(self.msg_format("protocol description"))
        self.logger.info(self.msg_format("num samples", self._num_samples))
        self.logger.info(self.msg_format("version", __version__))

        try:
            self.load_labware()
            self.load_instruments()
            self.setup_tip_log()
            self._button.color = 'white'
            self.msg = ""

            if self._debug_mode:
                self.dual_pause("debug mode", home=(False, False))

            self.body()

            self.assert_run_stage_has_been_executed()

            self.cleanup()

            if not self._ctx.is_simulating():
                self._sound_manager.play("finish")

        except Exception as e:
            self.logger.error("Exception occurred during protocol: {}".format(e))
            if not self._ctx.is_simulating():
                self.log_protocol_exception(e)
                self._sound_manager.play("alarm")
            raise e     # Propagate the exception
        finally:
            self.status = "finished"
            if not self._ctx.is_simulating():
                self._request.join(2, 0.5)
            self._watchdog.stop()
            self.track_tip()
            self._button.color = 'blue'
        self._mov_manager.move_to_home(force=True)    # Forcing the gantry to move away from back position
                                                      # on some robots the home current is not enough to move the gantry
        self._sound_manager.cleanup()
    
    def simulate(self):
        from opentrons import simulate
        self.run(simulate.get_protocol_api(self.metadata["apiLevel"]))


class WatchDog(Exception):
    def __init__(self, handler=None, logger=logging.getLogger(__name__)):
        self._logger = logger
        self._handler = handler if handler is not None else self.default_handler
        self._timer = None
        self._logger.debug("Initialization finished :-)")

    def start(self, timeout: int = 180):
        self._logger.debug("Starting watchdog with timeout time {}s".format(timeout))
        self._timer = Timer(timeout, self._handler)
        self._timer.start()

    def stop(self):
        self._logger.debug("Stopping watchdog")
        if self._timer is not None:
            self._timer.cancel()

    def reset(self, timeout: int = 180):
        self.stop()
        self.start(timeout)

    def default_handler(self):
        self._logger.info("Default timeout handler reached.")



# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
