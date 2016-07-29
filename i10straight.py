#!/usr/bin/env dls-python2.7
#i10straight
# Contains Straight
# Calls i10simulation

import numpy as np
import scipy.constants

import i10simulation
import i10controls


class RealModeController(object):
    """Controls simulation using the camonitored offsets/scales from PvMonitors."""

    def __init__(self):
        self.pvm = i10controls.PvMonitors.get_instance()
        self.pvm.register_straight_listener(self.update)
        self.straights = []

    def update(self, key, index): # need index?

        """Update scales whenever they change."""

        if key == i10controls.ARRAYS.SCALES:
            for straight in self.straights:
                straight.set_scales(self.pvm.get_scales())

        elif key == i10controls.ARRAYS.OFFSETS:
            for straight in self.straights:
                straight.set_offsets(self.pvm.get_offsets())

    def register_straight(self, straight):
        self.straights.append(straight)

    def deregister_straight(self, straight):
        self.straights.remove(straight)

    

class SimModeController(object):
    """Controls simulation using the simulated values from SimWriter."""
    def __init__(self):
        self.sim_writer = i10controls.SimWriter.get_instance()
        self.sim_writer.register_listener(self.update_sim)
        self.straights = []

    def update_sim(self, key):

        if key == i10controls.ARRAYS.SCALES:
            for straight in self.straights:
                straight.set_scales(self.sim_writer.simulated_scales)

        if key == i10controls.ARRAYS.OFFSETS:
            for straight in self.straights:
                straight.set_offsets(self.sim_writer.simulated_offsets)

    def register_straight(self, straight):
        self.straights.append(straight)

    def deregister_straight(self, straight):
        self.straights.remove(straight)


class Straight(object):

    """
    The physics of the I10 straight.

    Takes currents and converts them to time dependent kicks.
    Takes layout of the straight, applies these kicks to electron
    beam and produces photon beams at the insertion devices.
    """

    BEAM_RIGIDITY = 3e9/scipy.constants.c # hwat is this?
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])

    def __init__(self):

        """Get layout of straight, initialise values of PVs and link them
        up to listen to the monitored PV values."""

        self.data = i10simulation.Layout('config.txt')
        self.scales = i10controls.PvMonitors.get_instance().get_scales() # ?? do i want to instantiate this here??
        self.offsets = i10controls.PvMonitors.get_instance().get_offsets()

    def set_scales(self, scales):

        self.scales = scales

    def set_offsets(self, offsets):

        self.offsets = offsets

    def current_to_kick(self, current):

        """
        Convert currents (Amps) to fields (Tesla) and then to kick
        strength.
        """

        field = current * self.AMP_TO_TESLA
        kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in field])
        return kick

    def calculate_strengths(self, t):

        """Calculate time-varying strengths of kicker magnets.
            Args:
                t (int): time in sec
            Returns:
                new kicker strengths (array of x by y)
        """

        kick = self.current_to_kick(self.scales) * 0.5 * np.array([ # have I got the physics right for the scales and offsets?
                   np.sin(t*np.pi/100) + 1, 
                   -(np.sin(t*np.pi/100) + 1),
                   2,
                   np.sin(t*np.pi/100) - 1,
                  -np.sin(t*np.pi/100) + 1]) + self.current_to_kick(self.offsets)

        return kick

    def strength_setup(self, strength_values): # put underscore at start

        """Apply strengths to kickers."""

        for kicker, strength in zip(self.data.kickers, strength_values):
            kicker.set_strength(strength)

    def timestep(self, t):

        """
        Return positions and velocities of electron and photon beams at
        time t.
        """

        self.strength_setup(self.calculate_strengths(t))
        e_beam, p_beam = self.data.send_electrons_through()

        return e_beam, p_beam

    def p_beam_range(self, strength_values):

        """
        Calculate beams defining maximum range through which the
        photon beams sweep during a cycle.
        """

        self.strength_setup(self.current_to_kick(self.scales) * strength_values
                          + self.current_to_kick(self.offsets))

        p_beam = self.data.send_electrons_through()[1]

        return p_beam

    def p_beam_lim(self, currents): # use camonitor values... not yet connected

        """
        Calculate the photon beam produced by magnets at their maximum
        strength settings.
        """

        kick_limits = self.current_to_kick(currents)
        self.strength_setup(kick_limits)
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

