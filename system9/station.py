from .utils import ProtocolContextLoggingHandler, logging
from functools import wraps
from typing import Optional, Callable, Any


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


class Station:
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
