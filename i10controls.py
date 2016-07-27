#i10controls.py

import cothread
from cothread.catools import *

class SingletonType(type):

    """
    Singleton metaclass.

    Use as '__metaclass__ = SingletonType' in order
    to provide only one instance of your class each
    time the constructor is called.
    """

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(SingletonType, cls).__call__(*args, **kwargs)
            return cls.__instance


class PvMonitors(object):

    """
    The link between GUI and PVs.

    Monitors PVs, informs listeners when they 
    are changed and inputs new PV values. This
    is a singleton class, calling the constructor
    multiple times yields the same instance.
    """

    __metaclass__ = SingletonType

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

        """Monitor values of PVs: offsets, scales etc."""

        self.arrays = {
                      self.ARRAYS.OFFSETS: caget([
                                    ctrl + ':OFFSET' for ctrl in self.CTRLS]),
                      self.ARRAYS.SCALES: caget([
                                    ctrl + ':WFSCA' for ctrl in self.CTRLS]),
                      self.ARRAYS.SET_SCALES: caget([
                                    name + ':SETWFSCA' for name in self.NAMES]),
                      self.ARRAYS.WAVEFORMS: caget(self.TRACES),
                      self.ARRAYS.IMIN: caget([
                                    name + ':IMIN' for name in self.NAMES]),
                      self.ARRAYS.IMAX: caget([
                                    name + ':IMAX' for name in self.NAMES]),
                      self.ARRAYS.ERRORS: caget([
                                    name + ':ERRG' for name in self.NAMES])
                      }

        self.listeners = {'straight': [], 'trace': []}

        for i in range(len(self.CTRLS)):
            camonitor(self.CTRLS[i] + ':OFFSET',
                lambda x, i=i: self.update_values(x, self.ARRAYS.OFFSETS, i, 'straight'))
            camonitor(self.CTRLS[i] + ':WFSCA',
                lambda x, i=i: self.update_values(x, self.ARRAYS.SCALES, i, 'straight'))
            camonitor(self.NAMES[i] + ':SETWFSCA',
                lambda x, i=i: self.update_values(x, self.ARRAYS.SET_SCALES, i, 'straight'))
            camonitor(self.NAMES[i] + ':IMIN',
                lambda x, i=i: self.update_values(x, self.ARRAYS.IMIN, i, 'straight'))
            camonitor(self.NAMES[i] + ':IMAX',
                lambda x, i=i: self.update_values(x, self.ARRAYS.IMAX, i, 'straight'))
            camonitor(self.NAMES[i] + ':ERRG',
                lambda x, i=i: self.update_values(x, self.ARRAYS.ERRORS, i, 'straight'))
        for i in range(len(self.TRACES)):
            camonitor(self.TRACES[i],
                lambda x, i=i: self.update_values(x, self.ARRAYS.WAVEFORMS, i, 'trace'))

    def register_straight_listener(self, l):
        """Add new listener function to the list."""
        self.listeners['straight'].append(l)

    def register_trace_listener(self, l):
        self.listeners['trace'].append(l)

    def update_values(self, val, key, index, listener_key):
        """Update arrays and tell listeners when a value has changed."""
        self.arrays[key][index] = val
        [l(key, index) for l in self.listeners[listener_key]]

    def set_new_pvs(self, pvs, values):
        caput(pvs, values)





