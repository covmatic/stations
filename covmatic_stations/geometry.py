import math


class LysisTube:
    """Geometrical model of the Lysis Buffer tube"""
    def __init__(self, radius: float, cone_height: float = 0, fill: float = 0):
        self.radius = radius
        self._ch = cone_height
        self.volume = fill

    @property
    def height(self) -> float:
        r"""Height from inverse formula of setter

        H > h => V > pi * r^2 * h / 3
        (H - h) + h^3 / (3h^2) = V / (pi * r^2) => H = V / (pi * r^2) + 2/3 * h

        H < h => V < pi * r^2 * h / 3
        0 + H^3 / (3h^2) = V / (pi * r^2) => H = cbrt(3h^2 * V / (pi * r^2))
        """
        if self.volume > math.pi * self.radius**2 * self._ch / 3:
            # Filled more than the cone
            return self.volume / (math.pi * self.radius**2) + 2 * self._ch / 3
        else:
            # Filled less than the entire cone
            return (3 * self._ch**2 * self.volume / (math.pi * self.radius**2))**(1/3)

    @height.setter
    def height(self, value: float):
        r"""Volume is the cone volume plus the cylinder volume

        V = max(v - h, 0) * pi * r^2 + min(v, h)^3 * pi / 3 * r^2 / h^2
        V = [max(v - h, 0) + min(v, h)^3 / (3h^2)] * pi * r^2
        """
        self.volume = (
            max(value - self._ch, 0) +                 # cylinder starts at the end of the cone
            min(value, self._ch)**3 / (3*self._ch**2)  # cone ends at self._ch height
        ) * math.pi * self.radius**2

    def extract(self, volume: float) -> float:
        self.volume -= volume
        return self.height

    def fill(self, volume: float):
        self.volume += volume

    def refill(self, volume: float):
        self.volume = volume

    def __str__(self) -> str:
        return "{} with cone radius {:.2f} and height {:.2f} (mm)".format(type(self).__name__, self.radius, self._ch)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
