#!/usr/bin/env dls-python2.7
# controls.py
# Contains PvReferences, Arrays, PvMonitors

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


class Arrays(object):
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
            Arrays.OFFSETS: caget(
                [ctrl + ':OFFSET' for ctrl in PvReferences.CTRLS]),
            Arrays.SCALES: caget(
                [ctrl + ':WFSCA' for ctrl in PvReferences.CTRLS]),
            Arrays.SET_SCALES: caget(
                [name + ':SETWFSCA' for name in PvReferences.NAMES]),
            Arrays.WAVEFORMS: caget(PvReferences.TRACES),
            Arrays.SETI: caget([name + ':SETI' for name in PvReferences.NAMES]),
            Arrays.IMIN: caget([name + ':IMIN' for name in PvReferences.NAMES]),
            Arrays.IMAX: caget([name + ':IMAX' for name in PvReferences.NAMES]),
            Arrays.ERRORS: caget(
                [name + ':ERRGSTR' for name in PvReferences.NAMES])
        }

        self.listeners = {'straight': [], 'trace': []}

        for i in range(len(PvReferences.CTRLS)):
            camonitor(PvReferences.CTRLS[i] + ':OFFSET',
                      lambda x, i=i: self.update_values(
                    x, Arrays.OFFSETS, i, 'straight'))
            camonitor(PvReferences.CTRLS[i] + ':WFSCA',
                      lambda x, i=i: self.update_values(
                    x, Arrays.SCALES, i, 'straight'))

        for idx, ioc in enumerate(PvReferences.NAMES):
            camonitor(ioc + ':SETWFSCA',
                      lambda x, i=idx: self.update_values(
                    x, Arrays.SET_SCALES, i, 'straight'))
            camonitor(ioc + ':SETI',
                      lambda x, i=idx: self.update_values(
                    x, Arrays.SETI, i, 'straight'))
            camonitor(ioc + ':IMIN',
                      lambda x, i=idx: self.update_values(
                    x, Arrays.IMIN, i, 'straight'))
            camonitor(ioc + ':IMAX',
                      lambda x, i=idx: self.update_values(
                    x, Arrays.IMAX, i, 'straight'))
            camonitor(ioc + ':ERRGSTR',
                      lambda x, i=idx: self.update_values(
                    x, Arrays.ERRORS, i, 'straight'), format=FORMAT_TIME)

        camonitor(PvReferences.TRACES[0], lambda x: self.update_values(x, Arrays.WAVEFORMS, 0, 'trace'))
        camonitor(PvReferences.TRACES[1], lambda x: self.update_values(x, Arrays.WAVEFORMS, 1, 'trace'))

        cothread.Yield()  # Ensure monitored values are connected

    def register_straight_listener(self, l):
        """Add new listener function to the list."""
        self.listeners['straight'].append(l)

    def register_trace_listener(self, l):
        self.listeners['trace'].append(l)

    def update_values(self, val, key, index, listener_key):
        """Update arrays and tell listeners when a value has changed."""
        self.arrays[key][index] = val
        for l in self.listeners[listener_key]:
            l(key, index)

    def get_offsets(self):
        return self._get_array_value(Arrays.OFFSETS)

    def get_scales(self):
        return self._get_array_value(Arrays.SCALES)

    def get_set_scales(self):
        return self._get_array_value(Arrays.SET_SCALES)

    def get_actual_offsets(self):
        return self._get_array_value(Arrays.SETI)

    def get_max_currents(self):
        return self._get_array_value(Arrays.IMAX)

    def get_min_currents(self):
        return self._get_array_value(Arrays.IMIN)

    def get_errors(self):
        return self._get_array_value(Arrays.ERRORS)

    def get_cache(self):

        cache = {}
        for i in range(5):
            cache['%02d' % i] = {
                Arrays.OFFSETS: self._get_array_value(Arrays.OFFSETS)[i],
                Arrays.SCALES: self._get_array_value(Arrays.SCALES)[i]
            }
        return cache

    def _get_array_value(self, array_key):
        return self.arrays[array_key]
