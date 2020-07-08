from .a import StationA
import math


class StationAReload(StationA):
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
        
        self.logger.info("using {} samples per time. Refills needed: {}.".format(self.max_samples_per_set, refills))
        for set_idx in reversed(range(self.sets_of_samples)):
            self.logger.debug("{} remaining samples".format(self.remaining_samples))
            for s, d in zip(self._sources[:self.remaining_samples], self._dests_single[self._done_samples:]):
                self.transfer_sample(s, d)
                self._done_samples += 1
            if set_idx:
                self.logger.info("Please refill {} samples".format(min(self.remaining_samples, self.max_samples_per_set)))
                self._ctx.pause()
