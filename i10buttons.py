#!/usr/bin/env dls-python2.7
#i10buttons
# Contains ButtonData, OverCurrentException, MagnetCoordinator, Moves

from cothread.catools import caget, caput, FORMAT_TIME
import numpy as np
from PyQt4 import QtGui

from i10controls import PvMonitors


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
    Control jogs applied to magnets.

    Contains information about jogs to be applied to magnet scales and
    offsets, applies these jogs to the values given to it and
    checks this doesn't send the values over the magnet current limits.
    """

    BUTTON_DATA = {
        Moves.STEP_K3: np.array([0, 0, 1e-2, 0, 0]),
        Moves.BUMP_LEFT: np.array([23.2610, -23.2145, 10.1888, 0, 0]) / 600,
        Moves.BUMP_RIGHT: np.array([0, 0, 10.1888, -23.1068, 23.0378]) / 600,
        Moves.BPM1: np.array([136.71614094, 135.51675771, 0, -128.72713879,
                          -127.34037684])*1e-4,
        Moves.BPM2: np.array([-128.7237158, -129.31031648, 0, 134.90558954,
                           135.24691079])*1e-4,
        Moves.SCALE: np.array([1e-2, 1e-2, 0, 1e-2, 1e-2]),
        }

    def __init__(self): # does it matter that it's initialised 3 times or should I pass it as an argument to the writers from the gui?
        pass

    def jog(self, old_values, ofs, factor, jog_scale):

        """Increment the list of PVs by the appropriate offset from the list."""

        ofs = factor * self.BUTTON_DATA[ofs] * jog_scale

        values = old_values + ofs

        self._check_bounds(ofs)

        return values

    def _check_bounds(self, ofs):

        """Raises exception if new value exceeds magnet current limit."""

        pvm = PvMonitors.get_instance()
        scales = [abs(scale) for scale in pvm.get_scales()]
        offsets = pvm.get_offsets()
        imaxs = pvm.get_max_currents()
        imins = pvm.get_min_currents()

        # Check errors on limits.
        for idx, (max_val, min_val, offset, scale, new_val) in enumerate(
                zip(imaxs, imins, offsets, scales, ofs)):
            high = offset + new_val + scale
            low = offset + new_val - scale
            if high > max_val or low < min_val:
                raise OverCurrentException(idx) # this doesn't work in simulation mode BUT got the limits on the graph as a visual guide instead...
