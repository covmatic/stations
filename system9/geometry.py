import math


class LysisTube:
    """Geometrical model of the Lysis Buffer tube"""
    def __init__(self, radius: float, cone_height: float = 0, fill: float = 0):
        self.radius = radius 
        self._ch = cone_height
        self.volume = fill
    
    @property
    def height(self) -> float:
        return min(((3 * self._ch**2 * self.volume)/(math.pi * self.radius**2))**(1/3), self._ch) + max((self.volume / (math.pi * self.radius**2)) - (self._ch / 3), 0)
    
    @height.setter
    def height(self, value: float):
        self.volume = (math.pi * self.radius * self.radius) * (((min(value, self._ch)**3 / (3 * self._ch**2)) if self._ch > 0 else 0) + max(value - self._ch, 0))
    
    def extract(self, volume: float) -> float:
        self.volume -= volume
        return self.height
    
    def fill(self, volume: float):
        self.volume += volume
    
    def refill(self, volume: float):
        self.volume = volume
