from opentrons.protocol_api import ProtocolContext
from typing import Callable, Optional
from threading import Thread
import cherrypy
import time
import os


DEFAULT_REST_KWARGS = dict(
    favicon_url="https://opentrons.com/icons/icon-48x48.png",
    config={
        "global": {
            "server.socket_host": "0.0.0.0",
            "server.socket_port": 8080,
            "engine.autoreload.on": False,
        },
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": "/tmp/ot2-favicon.png",
        },
    }
)


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
    
    def __init__(self, ctx: ProtocolContext, config: Optional[dict] = None, favicon_url: Optional[str] = None):
        super(StationRESTServer, self).__init__()
        self._ctx = ctx
        self._config = config
        self._icon_url = favicon_url
    
    @cherrypy.expose
    def kill(self, delay: str = '1'):
        KillerThread(delay=float(delay)).start()

    @staticmethod
    def stop():
        cherrypy.engine.exit()


class StationRESTServerThread(StationRESTServer, Thread):
    def run(self):
        if self._icon_url and self._config and "tools.staticfile.filename" in self._config.get("/favicon.ico", {}):
            os.system("wget {} -O {}".format(self._icon_url, self._config["/favicon.ico"]["tools.staticfile.filename"]))
        cherrypy.quickstart(self, config=self._config)
    
    def join(self, timeout=None, after: float = 0):
        if after:
            time.sleep(after)
        self.stop()
        super(StationRESTServerThread, self).join(timeout=timeout)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.