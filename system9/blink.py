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
