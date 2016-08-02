from cothread.catools import caput
from i10controls import PvReferences, PvMonitors, ARRAYS
import numpy as np

import i10buttons


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

    def __init__(self):

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

    def __init__(self):

        AbstractWriter.__init__(self)
        self.simulated_offsets = np.array([0, 0, 0, 0, 0])
        self.simulated_scales =  np.array([23.2610, 23.2145,
                                          10.188844, 23.106842, 23.037771]) # like this or start with a caget??
        self.controllers = []

    def register_controller(self, controller):
        """Add new listener function to the list."""
        self.controllers.append(controller)

    def write(self, key, factor, jog_scale):
        if key == i10buttons.Moves.SCALE:
            jog_values = self.magnet_coordinator.jog(self.simulated_scales, key, factor, jog_scale)
        else:
            jog_values = self.magnet_coordinator.jog(self.simulated_offsets, key, factor, jog_scale)

        self.update_sim_values(key, jog_values)

    def update_sim_values(self, key, jog_values):
        if key == i10buttons.Moves.SCALE:
            self.simulated_scales = jog_values
            [c(ARRAYS.SCALES, jog_values) for c in self.controllers]
        else:
            self.simulated_offsets = jog_values
            [c(ARRAYS.OFFSETS, jog_values) for c in self.controllers]

    def reset(self):
        self.simulated_scales =  np.array([23.2610, 23.2145,
                                          10.188844, 23.106842, 23.037771])
        [c(ARRAYS.SCALES, self.simulated_scales) for c in self.controllers]
        self.simulated_offsets = np.array([0, 0, 0, 0, 0])
        [c(ARRAYS.OFFSETS, self.simulated_offsets) for c in self.controllers]