#!/usr/bin/env dls-python2.7
#i10buttons
# Contains ButtonData, OverCurrentException, Knobs

import cothread
from cothread.catools import caget, caput, FORMAT_TIME
import numpy as np
import scipy.io
import os
from PyQt4 import QtGui
from scipy.constants import c


# Alarm colours
ALARM_BACKGROUND = QtGui.QColor(255, 255, 255)
ALARM_COLORS = [
        QtGui.QColor(0, 215, 20), # None
        QtGui.QColor(255, 140, 0), # Minor
        QtGui.QColor(255, 0, 0), # Major
        QtGui.QColor(255, 0, 255), # Invalid
        ]


class OverCurrentException(Exception):
    def __init__(self, magnet_index):
        self.magnet_index = magnet_index


class Knobs(object):

    """
    Interface to control the I10 Fast Chicane and its simulation,
    enabling steering of the photon and electron beams.
    """

    MAGNET_STATUS_PV = 'SR10I-PC-FCHIC-01:GRPSTATE' # these probably shouldn't be in here
    BURT_STATUS_PV = 'CS-TI-BL10-01:BURT:OK'
    CYCLING_STATUS_PV = 'CS-TI-BL10-01:STATE'

    BUTTON_DATA = {
        'STEP_K3': np.array([0, 0, 1e-2, 0, 0]),
        'BUMP_LEFT': np.array([23.2610, 23.2145, 10.1888, 0, 0]) / 600,
        'BUMP_RIGHT': np.array([0, 0, 10.1888, 23.1068, 23.0378]) / 600,
        'BPM1': np.array([136.71614094, 135.51675771, 0, -128.72713879,
                          -127.34037684])*1e-4,
        'BPM2': np.array([-128.7237158, -129.31031648, 0, 134.90558954,
                           135.24691079])*1e-4,
        'SCALE': np.array([1e-2, 1e-2, 0, 1e-2, 1e-2]),
        'SET_SCALE': np.array([1e-2, 1e-2, 0, 1e-2, 1e-2])
        }


    def __init__(self, straight):

        self.jog_scale = 1.0
        self.straight = straight

    def jog(self, pvs, old_values, ofs, factor):

        """
        Increment the list of PVs by the offset. Errors are created
        when a user is likely to exceed magnet tolerances.
        """

        ofs = factor * self.BUTTON_DATA[ofs] * self.jog_scale

        values = old_values + ofs

        print
        for name, old, new in zip(pvs, old_values, values):
            print '%s:\t%f->%f' % (name, old, new)

        scales = [abs(scale) for scale in self.straight.scales]
        offsets = self.straight.offsets
        imaxs = self.straight.imax
        imins = self.straight.imin

        # Check errors on limits.
        for n in range(len(pvs)):
            max = imaxs[n]
            min = imins[n]
            offset = offsets[n]
            scale = scales[n]
            new_val = ofs[n]
            high = offset + new_val + scale
            low = offset + new_val - scale
            if high > max or low < min:
                print 'Warning: Setting current value above limits:'
                print ('%s: High: %f\tLow: %f\tMin: %f\tMax: %f\n'
                        % (pvs[n], high, low, max, min))
                raise OverCurrentException(n)

        return pvs, values

    def sim_offsets_scales(self, button, factor):

        """
        Increment the simulation magnet strengths by the offsets or scale
        factors.
        """

        if button == 'SCALE':
            self.straight.simulated_scales = (self.straight.simulated_scales
                        + (factor*self.BUTTON_DATA[button] * self.jog_scale))
        elif button == 'SET_SCALE':
            pass
        else:
            self.straight.simulated_offsets = (self.straight.simulated_offsets
                        + (factor*self.BUTTON_DATA[button] * self.jog_scale))

    def sim_reset(self):

        """Remove all offsets and scale factors within simulation-only mode."""

        self.straight.simulated_offsets = np.array([0, 0, 0, 0, 0])
        self.straight.simulated_scales =  np.array([23.2610, 23.2145, 
                                          10.188844, 23.106842, 23.037771])

