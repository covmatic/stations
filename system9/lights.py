from opentrons.protocol_api import ProtocolContext
from threading import Thread
import time


class BlinkingLight(Thread):
    def __init__(self, ctx: ProtocolContext, t: float = 1):
        super(BlinkingLight, self).__init__()
        self._on = False
        self._ctx = ctx
        self._t = t
    
    def stop(self):
        self._on = False
        self.join()
    
    def run(self):
        self._on = True
        state = self._ctx._hw_manager.hardware.get_lights()
        while self._on:
            self._ctx._hw_manager.hardware.set_lights(rails=not self._ctx._hw_manager.hardware.get_lights())
            time.sleep(self._t)
        self._ctx._hw_manager.hardware.set_lights(rails=state)


class Button:
    _base_cols = ['red', 'green', 'blue']
    _all_cols = ['black', 'blue', 'green', 'cyan', 'red', 'magenta', 'yellow', 'white']
    
    def __init__(self, ctx: ProtocolContext, color: str = 'blue'):
        self._ctx = ctx
        self._default_color = color
        self.color = color

    @classmethod
    def decode(cls, state: dict) -> str:
        return cls._all_cols[sum(1 << i for i, c in enumerate(reversed(cls._base_cols)) if state[c])]

    @classmethod
    def encode(cls, color: str) -> dict:
        idx = cls._all_cols.index(color) if color in cls._all_cols else 0
        return dict(zip(cls._base_cols, map(bool, map(int, bin(idx)[2:5].zfill(3)))))
    
    @property
    def color(self) -> str:
        return self.decode(self._state)

    @color.setter
    def color(self, color: str):
        self._state = self.encode(color)
        self._ctx._hw_manager.hardware._backend.gpio_chardev.set_button_light(**self._state)
    
    def __del__(self):
        self.color = self._default_color
