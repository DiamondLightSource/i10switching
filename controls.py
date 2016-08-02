#i10controls.py

import cothread
from cothread.catools import caget, camonitor, FORMAT_TIME


class PvReferences(object):
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

    MAGNET_STATUS_PV = 'SR10I-PC-FCHIC-01:GRPSTATE'
    BURT_STATUS_PV = 'CS-TI-BL10-01:BURT:OK'
    CYCLING_STATUS_PV = 'CS-TI-BL10-01:STATE'


class ARRAYS(object):
    OFFSETS = 'offsets'
    SCALES = 'scales'
    SET_SCALES = 'set_scales'
    WAVEFORMS = 'waveforms'
    SETI = 'seti'
    IMIN = 'imin'
    IMAX = 'imax'
    ERRORS = 'errors'


class PvMonitors(object):

    """
    The link between GUI and PVs.

    Monitors PVs, informs listeners when they 
    are changed and inputs new PV values. This
    is a singleton class, calling the constructor
    multiple times yields the same instance.
    """

    __instance = None
    __guard = True

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__guard = False
            cls.__instance = PvMonitors()
            cls.__guard = True
        return PvMonitors.__instance

    def __init__(self):

        """Monitor values of PVs: offsets, scales etc."""

        if self.__guard:
            raise RuntimeError('Do not instantiate. ' +
                               'If you require an instance use get_instance.')

        self.arrays = {
            ARRAYS.OFFSETS: caget(
                [ctrl + ':OFFSET' for ctrl in PvReferences.CTRLS]),
            ARRAYS.SCALES: caget(
                [ctrl + ':WFSCA' for ctrl in PvReferences.CTRLS]),
            ARRAYS.SET_SCALES: caget(
                [name + ':SETWFSCA' for name in PvReferences.NAMES]),
            ARRAYS.WAVEFORMS: caget(PvReferences.TRACES),
            ARRAYS.SETI: caget([name + ':SETI' for name in PvReferences.NAMES]),
            ARRAYS.IMIN: caget([name + ':IMIN' for name in PvReferences.NAMES]),
            ARRAYS.IMAX: caget([name + ':IMAX' for name in PvReferences.NAMES]),
            ARRAYS.ERRORS: caget(
                [name + ':ERRGSTR' for name in PvReferences.NAMES])
        }

        self.listeners = {'straight': [], 'trace': []}

        for i in range(len(PvReferences.CTRLS)):
            camonitor(PvReferences.CTRLS[i] + ':OFFSET',
                lambda x, i=i: self.update_values(
                    x, ARRAYS.OFFSETS, i, 'straight'))
            camonitor(PvReferences.CTRLS[i] + ':WFSCA',
                lambda x, i=i: self.update_values(
                    x, ARRAYS.SCALES, i, 'straight'))

        for idx, ioc in enumerate(PvReferences.NAMES):
            camonitor(ioc + ':SETWFSCA',
                lambda x, i=idx: self.update_values(
                    x, ARRAYS.SET_SCALES, i, 'straight'))
            camonitor(ioc + ':SETI',
                lambda x, i=idx: self.update_values(
                    x, ARRAYS.SETI, i, 'straight'))
            camonitor(ioc + ':IMIN',
                lambda x, i=idx: self.update_values(
                    x, ARRAYS.IMIN, i, 'straight'))
            camonitor(ioc + ':IMAX',
                lambda x, i=idx: self.update_values(
                    x, ARRAYS.IMAX, i, 'straight'))
            camonitor(ioc + ':ERRGSTR',
                lambda x, i=idx: self.update_values(
                    x, ARRAYS.ERRORS, i, 'straight'), format=FORMAT_TIME)

        for i in range(len(PvReferences.TRACES)):
            camonitor(PvReferences.TRACES[i],
                lambda x, i=i: self.update_values(
                    x, ARRAYS.WAVEFORMS, i, 'trace'))

        cothread.Yield()  # Ensure monitored values are connected

    def register_straight_listener(self, l):
        """Add new listener function to the list."""
        self.listeners['straight'].append(l)

    def register_trace_listener(self, l):
        self.listeners['trace'].append(l)

    def update_values(self, val, key, index, listener_key):
        """Update arrays and tell listeners when a value has changed."""
        self.arrays[key][index] = val
        [l(key, index) for l in self.listeners[listener_key]]

    def get_offsets(self):
        return self._get_array_value(ARRAYS.OFFSETS)

    def get_scales(self):
        return self._get_array_value(ARRAYS.SCALES)

    def get_set_scales(self):
        return self._get_array_value(ARRAYS.SET_SCALES)

    def get_actual_offsets(self):
        return self._get_array_value(ARRAYS.SETI)

    def get_max_currents(self):
        return self._get_array_value(ARRAYS.IMAX)

    def get_min_currents(self):
        return self._get_array_value(ARRAYS.IMIN)

    def get_errors(self):
        return self._get_array_value(ARRAYS.ERRORS)

    def get_cache(self):

        self.cache = c = {}
        for i in range(5):
            c['%02d' % i] = {
                ARRAYS.OFFSETS: self._get_array_value(ARRAYS.OFFSETS)[i],
                ARRAYS.SCALES: self._get_array_value(ARRAYS.SCALES)[i]
            }
        return c

    def _get_array_value(self, array_key):
        return self.arrays[array_key]
