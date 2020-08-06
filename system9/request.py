from opentrons.protocol_api import ProtocolContext 
from threading import Thread
import cherrypy


metadata = {'apiLevel': "2.5"}


class StationRESTServer:
    def __init__(self, ctx: ProtocolContext):
        super(StationRESTServer, self).__init__()
        self._ctx = ctx
    
    @cherrypy.expose
    def resume(self):
        self._ctx.resume()
    
    @cherrypy.expose
    def pause(self):
        self._ctx.pause()
    
    @staticmethod
    def stop():
        cherrypy.engine.exit()


class StationRESTServerThread(StationRESTServer, Thread):
    def run(self):
        cherrypy.quickstart(self)
    
    def join(self, timeout=None):
        self.stop()
        super(StationRESTServerThread, self).join()


def run(ctx: ProtocolContext):
    t = StationRESTServerThread(ctx)
    t.start()
    input("Press enter to stop")
    t.join()
