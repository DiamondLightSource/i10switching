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

import i10accelerators_ui
import i10beamline_ui

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
    Provides an interface to control the I10 Fast Chicane.
    The values are calculated to enable
    steering of the photon and electron beams.
    """

    NAMES = [
        'SR09A-PC-FCHIC-01',
        'SR09A-PC-FCHIC-02',
        'SR10S-PC-FCHIC-03',
        'SR10S-PC-FCHIC-04',
        'SR10S-PC-FCHIC-05']
    CTRLS = [
        'SR09A-PC-CTRL-01',
        'SR09A-PC-CTRL-02',
        'SR10S-PC-CTRL-03',
        'SR10S-PC-CTRL-04',
        'SR10S-PC-CTRL-05']

    MAGNET_STATUS_PV = 'SR10I-PC-FCHIC-01:GRPSTATE'
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
        'SCALE': np.array([1e-2, 1e-2, 0, 1e-2, 1e-2])
        }

    jog_scale = 1.0 # right place?

    def __init__(self):

        pass

    def get_imin(self):
        return caget([name + ':IMIN' for name in self.NAMES])

    def get_imax(self):
        return caget([name + ':IMAX' for name in self.NAMES])

    def get_offset(self):
        return caget([ctrl + ':OFFSET' for ctrl in self.CTRLS])

    def get_scale(self):
        return caget([name + ':SETWFSCA' for name in self.NAMES])

    def get_error(self):
        return caget([name + ':ERRG' for name in self.NAMES])

    def jog(self, pvs, ofs):
        """
        Increment the list of PVs by the offset.
        Errors are created when a user is likely to exceed magnet tolerances.
        """
        ofs = ofs * self.jog_scale

        old_values = caget(pvs)
        values = old_values + ofs

        print
        for name, old, new in zip(pvs, old_values, values):
            print '%s:\t%f->%f' % (name, old, new)

        scales = [abs(scale) for scale in self.get_scale()]
        offsets = self.get_offset()
        imaxs = self.get_imax()
        imins = self.get_imin()

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
        caput(pvs, values)


class SimulationButtons(object):

    def __init__(self, straight):

        self.knobs = Knobs()
        self.straight = straight

    def buttons(self, factor, button):

        self.straight.currents_add = self.straight.currents_add + (factor*np.array(
                            Knobs.BUTTON_DATA[button]) * self.knobs.jog_scale)

    def reconfigure(self, settings):

        self.straight.currents_add = settings

    def reset(self):

        self.straight.currents_add = np.array([0, 0, 0, 0, 0])

