#i10controls.py

import cothread
from cothread.catools import *
import numpy as np
import i10buttons

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

class ARRAYS(object):
    OFFSETS = 'offsets'
    SCALES = 'scales'
    SET_SCALES = 'set_scales'
    WAVEFORMS = 'waveforms'
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
                      ARRAYS.OFFSETS: caget([
                                    ctrl + ':OFFSET' for ctrl in PvReferences.CTRLS]),
                      ARRAYS.SCALES: caget([
                                    ctrl + ':WFSCA' for ctrl in PvReferences.CTRLS]),

                      ARRAYS.SET_SCALES: caget([
                                    name + ':SETWFSCA' for name in PvReferences.NAMES]),
                      ARRAYS.WAVEFORMS: caget(PvReferences.TRACES),
                      ARRAYS.IMIN: caget([
                                    name + ':IMIN' for name in PvReferences.NAMES]),
                      ARRAYS.IMAX: caget([
                                    name + ':IMAX' for name in PvReferences.NAMES]),
                      ARRAYS.ERRORS: caget([
                                    name + ':ERRG' for name in PvReferences.NAMES])
                      }

        self.listeners = {'straight': [], 'trace': []}

        for i in range(len(PvReferences.CTRLS)):
            camonitor(PvReferences.CTRLS[i] + ':OFFSET',
                lambda x, i=i: self.update_values(x, ARRAYS.OFFSETS, i, 'straight'))
            camonitor(PvReferences.CTRLS[i] + ':WFSCA',
                lambda x, i=i: self.update_values(x, ARRAYS.SCALES, i, 'straight'))

        for idx, ioc in enumerate(PvReferences.NAMES):
            camonitor(ioc + ':SETWFSCA',
                lambda x, i=idx: self.update_values(x, ARRAYS.SET_SCALES, i, 'straight'))
            camonitor(ioc + ':IMIN',
                lambda x, i=idx: self.update_values(x, ARRAYS.IMIN, i, 'straight'))
            camonitor(ioc + ':IMAX',
                lambda x, i=idx: self.update_values(x, ARRAYS.IMAX, i, 'straight'))
            camonitor(ioc + ':ERRG',
                lambda x, i=idx: self.update_values(x, ARRAYS.ERRORS, i, 'straight'))

        for i in range(len(PvReferences.TRACES)):
            camonitor(PvReferences.TRACES[i],
                lambda x, i=i: self.update_values(x, ARRAYS.WAVEFORMS, i, 'trace'))

        cothread.Yield()  # Ensure monitored values are connected

    def register_straight_listener(self, l):
        """Add new listener function to the list."""
        self.listeners['straight'].append(l)

    def register_trace_listener(self, l):
        self.listeners['trace'].append(l)

    def update_values(self, val, key, index, listener_key):
        """Update arrays and tell listeners when a value has changed."""
        self.arrays[key][index] = val
        [l(key, index) for l in self.listeners[listener_key]] # why does this need to pass the index at all?

#    def set_new_pvs(self, pvs, values):
#        caput(pvs, values)

    # OR
    # @property
    # def offsets(self):
    def get_offsets(self):
        return self._get_array_value(ARRAYS.OFFSETS)

    def get_scales(self):
        return self._get_array_value(ARRAYS.SCALES)

    def get_set_scales(self):
        return self._get_array_value(ARRAYS.SET_SCALES)

    def get_max_currents(self):
        return self._get_array_value(ARRAYS.IMAX)

    def get_min_currents(self):
        return self._get_array_value(ARRAYS.IMIN)

    def _get_array_value(self, array_key):
        return self.arrays[array_key]


class AbstractWriter(object):

    """
    Abstract writer.

    Takes coordinated magnet moves keys and writes the values to a location. 
    """

    def __init__(self):
        self.magnet_coordinator = i10buttons.MagnetCoordinator()

    def write(move, factor):
        """
        
        """
        raise NotImplemented()


class PvWriter(AbstractWriter):

    """
    Write coordainted magnets moves to PV's on the machine.
    """


    __instance = None
    __guard = True

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__guard = False
            cls.__instance = PvWriter()
            cls.__guard = True
        return PvWriter.__instance # do I want this to be a singleton?


    def __init__(self):

        if self.__guard:
            raise RuntimeError('Do not instantiate. ' +
                               'If you require an instance use get_instance.')

        AbstractWriter.__init__(self)
        self.scale_pvs = [ctrl + ':WFSCA' for ctrl in PvReferences.CTRLS]
        self.set_scale_pvs = [name + ':SETWFSCA' for name in PvReferences.NAMES]
        self.offset_pvs = [ctrl + ':OFFSET' for ctrl in PvReferences.CTRLS]

    def write(self, key, factor, jog_scale):
        if key == 'SCALE':
            scale_jog_values = self.magnet_coordinator.jog(PvMonitors.get_instance().get_scales(), key, factor, jog_scale)
            set_scale_jog_values = self.magnet_coordinator.jog(PvMonitors.get_instance().get_set_scales(), key, factor, jog_scale)
            self.write_to_pvs(self.scale_pvs, scale_jog_values)
            self.write_to_pvs(self.set_scale_pvs, set_scale_jog_values)
        else:
            offset_jog_values = self.magnet_coordinator.jog(PvMonitors.get_instance().get_offsets(), key, factor, jog_scale)
            self.write_to_pvs(self.offset_pvs, offset_jog_values)

    def write_to_pvs(self, pvs, jog_values):
            caput(pvs, jog_values)


class SimWriter(AbstractWriter):

    """
    Write coordainted magnets moves to the manual simulation controller.
    """

    __instance = None
    __guard = True

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__guard = False
            cls.__instance = SimWriter()
            cls.__guard = True
        return SimWriter.__instance # do I want this to be a singleton?

    def __init__(self):

        if self.__guard:
            raise RuntimeError('Do not instantiate. ' +
                               'If you require an instance use get_instance.')

        AbstractWriter.__init__(self)
        self.simulated_offsets = np.array([0, 0, 0, 0, 0])
        self.simulated_scales =  np.array([23.2610, 23.2145, 
                                          10.188844, 23.106842, 23.037771]) # like this or start with a caget??
        self.listeners = []

    def register_listener(self, l):
        """Add new listener function to the list."""
        self.listeners.append(l)

    def write(self, key, factor, jog_scale):
        if key == 'SCALE':
            jog_values = self.magnet_coordinator.jog(self.simulated_scales, key, factor, jog_scale)
        else:
            jog_values = self.magnet_coordinator.jog(self.simulated_offsets, key, factor, jog_scale)

        self.update_sim_values(key, jog_values)

    def update_sim_values(self, key, jog_values):
        if key == 'SCALE':
            self.simulated_scales = jog_values
            [l(ARRAYS.SCALES) for l in self.listeners]
        else:
            self.simulated_offsets = jog_values
            [l(ARRAYS.OFFSETS) for l in self.listeners]

    def reset(self):
        self.simulated_scales =  np.array([23.2610, 23.2145, 
                                          10.188844, 23.106842, 23.037771])
        [l(ARRAYS.SCALES) for l in self.listeners]
        self.simulated_offsets = np.array([0, 0, 0, 0, 0])
        [l(ARRAYS.OFFSETS) for l in self.listeners]




