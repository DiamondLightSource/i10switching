#!/usr/bin/env dls-python2.7
#i10buttons
# Contains ButtonData, OverCurrentException, MagnetCoordinator

from cothread.catools import caget, caput, FORMAT_TIME
import numpy as np
from PyQt4 import QtGui

from i10controls import PvMonitors


# Alarm colours
ALARM_BACKGROUND = QtGui.QColor(255, 255, 255)
ALARM_COLORS = [
        QtGui.QColor(0, 215, 20), # None
        QtGui.QColor(255, 140, 0), # Minor
        QtGui.QColor(255, 0, 0), # Major
        QtGui.QColor(255, 0, 255), # Invalid
        ]
class Moves(object):
    STEP_K3 = 0
    BUMP_LEFT = 1
    BUMP_RIGHT = 2
    BPM1 = 3
    BPM2 = 4
    SCALE = 5 # should this be a subclass of MagnetCoordinator?


class OverCurrentException(Exception):
    def __init__(self, magnet_index):
        super(OverCurrentException, self).__init__()
        self.magnet_index = magnet_index


class MagnetCoordinator(object):

    """
    Interface to control the I10 Fast Chicane and its simulation,
    enabling steering of the photon and electron beams.
    """

    MAGNET_STATUS_PV = 'SR10I-PC-FCHIC-01:GRPSTATE' # these probably shouldn't be in here
    BURT_STATUS_PV = 'CS-TI-BL10-01:BURT:OK'
    CYCLING_STATUS_PV = 'CS-TI-BL10-01:STATE'


    BUTTON_DATA = {
        Moves.STEP_K3: np.array([0, 0, 1e-2, 0, 0]),
        Moves.BUMP_LEFT: np.array([23.2610, 23.2145, 10.1888, 0, 0]) / 600,
        Moves.BUMP_RIGHT: np.array([0, 0, 10.1888, 23.1068, 23.0378]) / 600,
        Moves.BPM1: np.array([136.71614094, 135.51675771, 0, -128.72713879,
                          -127.34037684])*1e-4,
        Moves.BPM2: np.array([-128.7237158, -129.31031648, 0, 134.90558954,
                           135.24691079])*1e-4,
        Moves.SCALE: np.array([1e-2, 1e-2, 0, 1e-2, 1e-2]),
        }


    def __init__(self): # why initialised 3 times??
        pass
#        self.jog_scale = 1.0


    def jog(self, old_values, ofs, factor, jog_scale):

        """
        Increment the list of PVs by the offset. Errors are created
        when a user is likely to exceed magnet tolerances.
        """

        ofs = factor * self.BUTTON_DATA[ofs] * jog_scale

        values = old_values + ofs

        self._check_bounds(ofs)

        return values

    def _check_bounds(self, ofs):

        """
        Raises OverCurrentException if...
        """

        pvm = PvMonitors.get_instance()
        scales = [abs(scale) for scale in pvm.get_scales()]
        offsets = pvm.get_offsets()
        imaxs = pvm.get_max_currents()
        imins = pvm.get_min_currents()

        # Check errors on limits.
        for idx, (max_val, min_val, offset, scale, new_val) in enumerate(zip(imaxs, imins, offsets, scales, ofs)):
            high = offset + new_val + scale
            low = offset + new_val - scale
            if high > max_val or low < min_val:
                raise OverCurrentException(idx)


