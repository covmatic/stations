from opentrons.protocol_api import ProtocolContext
from threading import Thread
from functools import wraps
import requests
import time


class Dummyable(type):
    class Dummy: pass
    
    def __new__(mcs, classname: str, supers: tuple, classdict: dict):
        cls = super(Dummyable, mcs).__new__(mcs, classname, supers, classdict)
        if mcs.Dummy not in cls.__mro__:
            def emptyfun(*args, **kwargs): pass
            dummydict = {k: v if k[:2] == "__" else (wraps(v)(emptyfun) if callable(v) else None) for k, v in map(lambda k: (k, getattr(cls, k, None)), dir(cls))}
            cls.dummy = type("Dummy{}".format(classname), (mcs.Dummy, cls), dummydict)
        return cls


class BlinkingLight(Thread, metaclass=Dummyable):
    def __init__(self, ctx: ProtocolContext, t: float = 1):
        super(BlinkingLight, self).__init__()
        self._on = False
        self._state = True
        self._state_initial = None
        self._ctx = ctx
        self._t = t
    
    def stop(self):
        self._on = False
        self.join()
    
    def initial_state(self) -> bool:
        return self._ctx._hw_manager.hardware.get_lights()
    
    def set_light(self, s: bool):
        self._ctx._hw_manager.hardware.set_lights(rails=s)
    
    def run(self):
        self._on = True
        self._state_initial = self.initial_state()
        while self._on:
            self._state = not self._state
            self.set_light(self._state)
            time.sleep(self._t)
        self.set_light(self._state_initial)


class BlinkingLightHTTP(BlinkingLight):
    _URL = "http://127.0.0.1:31950/robot/lights"
    
    def initial_state(self) -> bool:
        return requests.get(self._URL).json().get('on', False)
    
    def set_light(self, s: bool):
        requests.post(self._URL, json={'on': s})


class Button(metaclass=Dummyable):
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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
