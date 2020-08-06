from . import __version__
from .utils import ProtocolContextLoggingHandler, logging
from .lights import Button, BlinkingLight
from opentrons.protocol_api import ProtocolContext
from opentrons.types import Point
from abc import ABCMeta, abstractmethod
from functools import wraps, partial
from itertools import chain, repeat
from opentrons.types import Location
from typing import Optional, Callable, Iterable, Tuple
import json
import math
import os
import logging


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


class Station(metaclass=ABCMeta):
    _protocol_description = "[BRIEFLY DESCRIBE YOUR PROTOCOL]"
    
    def __init__(self,
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_threshold: int = 296,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        samples_per_col: int = 8,
        skip_delay: bool = False,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/',
        tip_track: bool = False,
        **kwargs,
    ):
        self._drop_loc_l = drop_loc_l
        self._drop_loc_r = drop_loc_r
        self._drop_threshold = drop_threshold
        self.jupyter = jupyter
        self._logger = logger
        self.metadata = metadata
        self._num_samples = num_samples
        self._samples_per_col = samples_per_col
        self._skip_delay = skip_delay
        self._tip_log_filename = tip_log_filename
        self._tip_log_folder_path = tip_log_folder_path
        self._tip_track = tip_track
        self._ctx: Optional[ProtocolContext] = None
        self._drop_count = 0
        self._side_switch = True
    
    def __getattr__(self, item: str):
        return self.metadata[item]
    
    @property
    def logger(self) -> logging.getLoggerClass():
        if ((not hasattr(self, "_logger")) or self._logger is None) and self._ctx is not None:
            self._logger = logging.getLogger(self.logger_name)
            self._logger.addHandler(ProtocolContextLoggingHandler(self._ctx))
        return self._logger
    
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
        if self._tip_track:# and not self._ctx.is_simulating():
            self.logger.info("logging tip info in {}".format(self._tip_log_filepath))
            if os.path.isfile(self._tip_log_filepath):
                with open(self._tip_log_filepath) as json_file:
                    data: dict = json.load(json_file)
        else:
            self.logger.debug("not using tip log file")
        
        self._tip_log = {
            'count': {t: data.get(t, 0) for t in self._tipracks().keys()},
            'tips': {t: list(chain.from_iterable(map(first_row if getattr(self, p).channels > 1 else wells, getattr(self, t)))) for t, p in self._tipracks().items()},
        }
        self._tip_log['max'] = {t: len(p) for t, p in self._tip_log['tips'].items()}
    
    def track_tip(self):
        if self._tip_track:# and not self._ctx.is_simulating():
            self.logger.info("dumping logging tip info in {}".format(self._tip_log_filepath))
            os.makedirs(self._tip_log_folder_path, exist_ok=True)
            with open(self._tip_log_filepath, 'w') as outfile:
                json.dump(self._tip_log['count'], outfile)
    
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
                self.pause('before resuming, please replace {}'.format(", ".join(map(str, getattr(self, tiprack)))), blink=True)
                self._tip_log['count'][tiprack] = 0
            pip.pick_up_tip(self._tip_log['tips'][tiprack][self._tip_log['count'][tiprack]])
            self._tip_log['count'][tiprack] += 1
        else:
            pip.pick_up_tip(loc)
    
    def drop(self, pip):
        # Drop in the Fixed Trash (on 12) at different positions to avoid making a tall heap of tips
        drop_loc = self._ctx.loaded_labwares[12].wells()[0].top().move(Point(x=self._drop_loc_r if self._side_switch else self._drop_loc_l))
        self._side_switch = not self._side_switch
        pip.drop_tip(drop_loc)
        self._drop_count += pip.channels
        if self._drop_count >= self._drop_threshold:
            self.pause('pausing. Please empty tips from waste before resuming')
            self._drop_count = 0
    
    def pause(self,
        msg: str = "",
        blink: bool = False,
        blink_period: float = 2,
        color: str = 'red',
        delay_time: float = 16,
        home: bool = True,
        level: int = logging.INFO,
        pause: bool = True,
    ):
        old_color = self._button.color
        self._button.color = color
        if msg:
            self.logger.log(level, msg)
        if home:
            self._ctx.home()
        if blink:
            lt = BlinkingLight(self._ctx, t=blink_period/2)
            lt.start()
        if delay_time > 0:
            self._ctx.delay(delay_time)
        if blink:
            lt.stop()
        if pause:
            self._ctx.pause()
            self._ctx.delay(0.1)  # pad to avoid pause leaking
        self._button.color = old_color
    
    def delay(self,
        mins: float,
        msg: str = "",
        color: str = 'yellow',
        home: bool = True,
        level: int = logging.INFO,
    ):
        self.pause(
            msg="{} for {} minutes{}".format(msg, mins, ". Pausing for skipping delay. Please resume" if self._skip_delay else ""),
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
        self._ctx = ctx
        self._button = Button(self._ctx, 'blue')
        self.logger.info(self._protocol_description)
        self.logger.info("using system9 version {}".format(__version__))
        self.load_labware()
        self.load_instruments()
        self.setup_tip_log()
        self._button.color = 'white'
        
        self.body()
        
        self._button.color = 'blue'
        self.track_tip()
        self._ctx.home()
    
    def simulate(self):
        from opentrons import simulate
        self.run(simulate.get_protocol_api(self.metadata["apiLevel"]))
