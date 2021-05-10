import logging

class MultiTubeSource(object):
    """

    """
    def __init__(self, name="", logger=None):
        self._source_tubes_and_vol = []
        self._name = name
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)

    def append_tube_with_vol(self, source, available_volume):
        self._source_tubes_and_vol.append(dict(source=source,
                                               available_volume=available_volume))
        self.logger.debug("{}: appended {} with {}ul".format(self._name, source, available_volume))
        self.logger.debug("Now sources is: {}".format(self._source_tubes_and_vol))

    def aspirate_from_tubes(self, volume, pip, aspirate_height_from_bottom: float = 2):
        aspirate_list = []
        left_volume = volume
        for source_and_vol in self._source_tubes_and_vol:
            if source_and_vol["available_volume"] >= left_volume:
                # aspirate_list.append(dict(source=source_and_vol["source"], vol=left_volume))
                aspirate_vol = left_volume
            else:
                aspirate_vol = source_and_vol["available_volume"]
            left_volume -= aspirate_vol
            source_and_vol["available_volume"] -= aspirate_vol
            if aspirate_vol != 0:
                aspirate_list.append(dict(source=source_and_vol["source"], vol=aspirate_vol))

            if left_volume == 0:
                break
        else:
            raise Exception("{}: no volume left in source tubes.".format(self._name))

        for a in aspirate_list:
            pip.aspirate(a["vol"], a["source"].bottom(aspirate_height_from_bottom))

        self.logger.debug("{} sources: {}".format(self._name, self._source_tubes_and_vol))

    @property
    def locations_str(self):
        return "{}: ".format(self._name) + \
               " ".join(["{}; ".format(sv['source'])
                         for sv in self._source_tubes_and_vol])
    def __str__(self):
        return "{}: ".format(self._name) +\
               " ".join(["{} with volume {}ul;".format(sv['source'], sv['available_volume'])
                        for sv in self._source_tubes_and_vol])
