from .a import StationA
from ..station import StationMeta
import math


# Mixin allows for finer control over the mro
class StationAReloadMixin(metaclass=StationMeta):
    @property
    def max_samples_per_set(self) -> int:
        return len(self._sources)
    
    @property
    def sets_of_samples(self) -> int:
        return math.ceil(self._num_samples/self.max_samples_per_set)

    @property
    def remaining_samples(self) -> int:
        return self._num_samples - self._done_samples

    def transfer_samples(self):
        self._done_samples = 0
        refills = self.sets_of_samples - 1

        destinations = list(self.non_control_dests())

        self.logger.info(self.msg_format("refills", self.max_samples_per_set, refills))
        for set_idx in reversed(range(self.sets_of_samples)):
            self.logger.debug("{} remaining samples".format(self.remaining_samples))
            for s, d in zip(self._sources[:self.remaining_samples], self._dests_single[self._done_samples:]):
                if self.run_stage("transfer sample {}/{}".format(self._done_samples + 1, self._num_samples)):
                    if d in destinations:
                        self.transfer_sample(s, d)
                    else:
                        self._ctx.comment("Skipping transfer sample {}: is control".format(d))
                self._done_samples += 1
            if set_idx and self.run_stage("refill {}/{}".format(self.sets_of_samples - set_idx, self.sets_of_samples - 1)):
                self.request_dashboard_input(self.msg_format("refill", min(self.remaining_samples, self.max_samples_per_set)))

# Subclass is more straightforward
class StationAReload(StationAReloadMixin, StationA):
    pass


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
