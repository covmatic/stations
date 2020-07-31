from ..station import Station, labware_loader, instrument_loader
from opentrons.protocol_api import ProtocolContext
import logging
from typing import Optional


class StationC(Station):
    _protocol_description = "station C protocol"
    
    def __init__(
        self,
        drop_loc_l: float = 0,
        drop_loc_r: float = 0,
        drop_threshold: int = 296,
        jupyter: bool = True,
        logger: Optional[logging.getLoggerClass()] = None,
        metadata: Optional[dict] = None,
        num_samples: int = 96,
        samples_per_col: int = 8,
        skip_delay: bool = False,
        tip_log_filename: str = 'tip_log.json',
        tip_log_folder_path: str = './data/C',
        tip_track: bool = False,
    ):
        """ Build a :py:class:`.StationC`.
        :param drop_loc_l: offset for dropping to the left side (should be positive) in mm
        :param drop_loc_r: offset for dropping to the right side (should be negative) in mm
        :param drop_threshold: the amount of dropped tips after which the run is paused for emptying the trash
        :param logger: logger object. If not specified, the default logger is used that logs through the ProtocolContext comment method
        :param metadata: protocol metadata
        :param num_samples: The number of samples that will be loaded on the station B
        :param samples_per_col: The number of samples in a column of the destination plate
        :param skip_delay: If True, pause instead of delay.
        :param tip_log_filename: file name for the tip log JSON dump
        :param tip_log_folder_path: folder for the tip log JSON dump
        :param tip_track: If True, try and load previous tiprack log from the JSON file
        """
        super(StationC, self).__init__(
            drop_loc_l=drop_loc_l,
            drop_loc_r=drop_loc_r,
            drop_threshold=drop_threshold,
            jupyter=jupyter,
            logger=logger,
            metadata=metadata,
            num_samples=num_samples,
            samples_per_col=samples_per_col,
            skip_delay=skip_delay,
            tip_log_filename=tip_log_filename,
            tip_log_folder_path=tip_log_folder_path,
            tip_track=tip_track,
        )
        
    def _tiprack_log_args(self):
        return (), (), ()
    
    def run(self, ctx: ProtocolContext):
        super(StationC, self).run(ctx)


if __name__ == "__main__":
    StationC(metadata={'apiLevel': '2.3'}).simulate()
