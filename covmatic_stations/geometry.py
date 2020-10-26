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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
