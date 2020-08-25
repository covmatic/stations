from opentrons.protocol_api import ProtocolContext
from typing import Callable, Optional
from threading import Thread
import cherrypy
import time
import os


class ContextAPI(type):
    @staticmethod
    def context_api(method: str) -> Callable:
        return cherrypy.expose(lambda self: getattr(self._ctx, method)())
    
    def __new__(mcs, classname: str, supers: tuple, classdict: dict):
        classdict.update(zip(*(lambda a: (a, map(mcs.context_api, a)))(classdict.pop("_actions", []))))
        return super(ContextAPI, mcs).__new__(mcs, classname, supers, classdict)


class KillerThread(Thread):
    def __init__(self, delay: float = 1):
        super(KillerThread, self).__init__()
        self._t = delay
    
    def run(self):
        time.sleep(self._t)
        os.kill(os.getpid(), 9)  # 9 -> SIGKILL


class StationRESTServer(metaclass=ContextAPI):
    _actions = ["pause", "resume"]
    
    def __init__(self, ctx: ProtocolContext, config: Optional[dict] = None):
        super(StationRESTServer, self).__init__()
        self._ctx = ctx
        self._config = config
    
    @cherrypy.expose
    def kill(self, delay: str = '1'):
        KillerThread(delay=float(delay)).start()

    @staticmethod
    def stop():
        cherrypy.engine.exit()


class StationRESTServerThread(StationRESTServer, Thread):
    def run(self):
        cherrypy.quickstart(self, config=self._config)
    
    def join(self, timeout=None):
        self.stop()
        super(StationRESTServerThread, self).join()
