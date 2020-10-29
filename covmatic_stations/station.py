from . import __version__, __file__ as module_path
from .request import StationRESTServerThread, DEFAULT_REST_KWARGS
from .utils import ProtocolContextLoggingHandler, LocalWebServerLogger
from .lights import Button, BlinkingLightHTTP, BlinkingLight
from opentrons.protocol_api import ProtocolContext
from opentrons.types import Point
from opentrons import commands
from abc import ABCMeta, abstractmethod
from functools import wraps, partialmethod
from itertools import chain
from opentrons.types import Location
from typing import Optional, Callable, Tuple
import json
import math
import os
import logging
import time


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
        c = super(StationMeta, meta).__new__(meta, name, bases, classdict)
        try:
            with open(os.path.join(os.path.dirname(module_path), 'msg', '{}.json'.format(name))) as f:
                c._messages = json.load(f)
        except FileNotFoundError:
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
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_loc_y: float = 0,
        drop_threshold: int = 296,
        dummy_lights: bool = True,
        jupyter: bool = True,
        log_filepath: Optional[str] = '/var/lib/jupyter/notebooks/outputs/run_{}.log',
        log_lws_ip: Optional[str] = None,
        log_lws_endpoint: str = ":5002/log",
        logger: Optional[logging.getLoggerClass()] = None,
        language: str = "ENG",
        metadata: Optional[dict] = None,
        num_samples: int = 96,
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
        **kwargs,
    ):
        self._drop_loc_l = drop_loc_l
        self._drop_loc_r = drop_loc_r
        self._drop_loc_y = drop_loc_y
        self._drop_threshold = drop_threshold
        self._dummy_lights = dummy_lights
        self.jupyter = jupyter
        self._language = language
        self._log_filepath = log_filepath.format(time.strftime("%Y_%m_%d__%H_%M_%S"))
        self._log_lws_ip = log_lws_ip
        self._log_lws_endpoint = log_lws_endpoint
        self._logger = logger
        self.metadata = metadata
        self._num_samples = num_samples
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
        self.status = "initializing"
        self.stage = None
        self._msg = ""
        self.external = False
        self._run_stage = self._start_at is None
    
    def set_external(self, value: bool = True) -> bool:
        self.external = value
        return self.external
    
    set_internal = partialmethod(set_external, value=False)
    
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
        return self._run_stage
    
    @property
    def logger(self) -> logging.getLoggerClass():
        if ((not hasattr(self, "_logger")) or self._logger is None) and self._ctx is not None:
            self._logger = logging.getLogger(self.logger_name)
            self._logger.addHandler(ProtocolContextLoggingHandler(self._ctx))
        return self._logger
    
    def setup_opentrons_logger(self):
        stack_logger = logging.getLogger('opentrons')
        stack_logger.setLevel(self.logger.getEffectiveLevel())
        if self._log_filepath and (self._simulation_log_file or not self._ctx.is_simulating()):
            os.makedirs(os.path.dirname(self._log_filepath), exist_ok=True)
            stack_logger.addHandler(logging.FileHandler(self._log_filepath))
        self._lws_logger = LocalWebServerLogger(self._log_lws_ip, self._log_lws_endpoint)
        if self._simulation_log_lws or not self._ctx.is_simulating():
            self._ctx.broker.subscribe(commands.command_types.COMMAND, self._lws_logger)
    
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
    
    def setup_tip_log(self):
        data = {}
        if self._tip_track:
            self.logger.info(self.msg_format("tip info log", self._tip_log_filepath))
            if os.path.isfile(self._tip_log_filepath):
                with open(self._tip_log_filepath) as json_file:
                    data: dict = json.load(json_file).get("count", {})
        else:
            self.logger.debug("not using tip log file")
        
        self._tip_log = {
            'count': {t: data.get(t, 0) for t in self._tipracks().keys()},
            'tips': {t: list(chain.from_iterable(map(first_row if getattr(self, p).channels > 1 else wells, getattr(self, t)))) for t, p in self._tipracks().items()},
        }
        self._tip_log['max'] = {t: len(p) for t, p in self._tip_log['tips'].items()}
    
    def track_tip(self):
        if self._tip_track and not self._ctx.is_simulating():
            self.logger.debug(self.get_msg_format("tip log dump", self._tip_log_filepath))
            os.makedirs(self._tip_log_folder_path, exist_ok=True)
            with open(self._tip_log_filepath, 'w') as outfile:
                json.dump({
                    "count": self._tip_log['count'],
                    "next": {k: str(self._tip_log['tips'][k][v % self._tip_log['max'][k]]) for k, v in self._tip_log['count'].items()},
                }, outfile, indent=2)
    
    def pick_up(self, pip, loc: Optional[Location] = None, tiprack: Optional[str] = None):
        if loc is None:
            if tiprack is None:
                for t in self._tipracks().keys():
                    if getattr(self, t) == pip.tip_racks:
                        tiprack = t
                        break
            if tiprack is None:
                raise RuntimeError("no tiprack associated to pipette")
            
            if self._tip_log['count'][tiprack] == self._tip_log['max'][tiprack]:
                # If empty, wait for refill
                self._tip_log['count'][tiprack] = 0
                self.track_tip()
                self.pause(self.get_msg_format("refill tips", "\n".join(map(str, getattr(self, tiprack)))))
            self._tip_log['count'][tiprack] += 1
            self.track_tip()
            pip.pick_up_tip(self._tip_log['tips'][tiprack][self._tip_log['count'][tiprack] - 1])
        else:
            pip.pick_up_tip(loc)
    
    def drop(self, pip):
        # Drop in the Fixed Trash (on 12) at different positions to avoid making a tall heap of tips
        drop_loc = self._ctx.loaded_labwares[12].wells()[0].top().move(Point(x=self._drop_loc_r if self._side_switch else self._drop_loc_l, y=self._drop_loc_y))
        self._side_switch = not self._side_switch
        pip.drop_tip(drop_loc)
        self._drop_count += pip.channels
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
        self.status = "pause"
        old_color = self._button.color
        self._button.color = color
        if msg:
            self.msg = msg
            self.logger.log(level, self.msg)
        if home:
            self._ctx.home()
        if blink and not self._ctx.is_simulating():
            lt = (BlinkingLightHTTP if self._dummy_lights else BlinkingLight)(self._ctx, t=blink_period/2)
            lt.start()
        if delay_time > 0:
            self._ctx.delay(delay_time)
        if pause:
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
        
    def body(self):
        pass
    
    def run(self, ctx: ProtocolContext):
        self.status = "running"
        self._ctx = ctx
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
        
        self.load_labware()
        self.load_instruments()
        self.setup_tip_log()
        self._button.color = 'white'
        self.msg = ""
        
        try:
            self.body()
        finally:
            self.status = "finished"
            if not self._ctx.is_simulating():
                self._request.join(2, 0.5)
            self.track_tip()
            self._button.color = 'blue'
        self._ctx.home()
    
    def simulate(self):
        from opentrons import simulate
        self.run(simulate.get_protocol_api(self.metadata["apiLevel"]))


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
