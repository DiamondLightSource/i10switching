#i10controls.py

import cothread
from cothread.catools import *


class Controls(object):

    """Monitors PVs, informs listeners when they are changed and inputs new
    PV values."""

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

    TRACES = [
        'BL10I-EA-USER-01:WAI1',
        'BL10I-EA-USER-01:WAI2']


    class ARRAYS(object):
        OFFSETS = 'offsets'
        SCALES = 'scales'
        SET_SCALES = 'set_scales'
        WAVEFORMS = 'waveforms'
        IMIN = 'imin'
        IMAX = 'imax'
        ERRORS = 'errors'

    def __init__(self):
        self.arrays = {
               'offsets': caget([ctrl + ':OFFSET' for ctrl in self.CTRLS]),
               'scales': caget([ctrl + ':WFSCA' for ctrl in self.CTRLS]),
               'set_scales': caget([name + ':SETWFSCA' for name in self.NAMES]),
               'waveforms': caget(self.TRACES),
               'imin': caget([name + ':IMIN' for name in self.NAMES]),
               'imax': caget([name + ':IMAX' for name in self.NAMES]),
               'errors': caget([name + ':ERRG' for name in self.NAMES])
               }

        self.listeners = []

        for i in range(len(self.CTRLS)):
            camonitor(self.CTRLS[i] + ':OFFSET',
                    lambda x, i=i: self.update_values(x, 'offsets', i))
            camonitor(self.CTRLS[i] + ':WFSCA',
                    lambda x, i=i: self.update_values(x, 'scales', i))
            camonitor(self.NAMES[i] + ':SETWFSCA',
                    lambda x, i=i: self.update_values(x, 'set_scales', i)) #setwfsca vs wfsca...
            camonitor(self.NAMES[i] + ':IMIN',
                    lambda x, i=i: self.update_values(x, 'imin', i))
            camonitor(self.NAMES[i] + ':IMAX',
                    lambda x, i=i: self.update_values(x, 'imax', i))
            camonitor(self.NAMES[i] + ':ERRG',
                    lambda x, i=i: self.update_values(x, 'errors', i))
        for i in range(len(self.TRACES)):
            camonitor(self.TRACES[i],
                    lambda x, i=i: self.update_values(x, 'waveforms', i))

    def register_listener(self, l):

        """Adds new listener function to the list."""

        self.listeners.append(l)

    def update_values(self, val, key, index):

        """Updates arrays and tells listeners when a value has changed."""

        self.arrays[key][index] = val
        [l(key, index) for l in self.listeners]

    def set_new_pvs(self, pvs, values):

        caput(pvs, values)






