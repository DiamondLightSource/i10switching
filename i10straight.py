#!/usr/bin/env dls-python2.7
#i10straight
# Contains Straight
# Calls i10simulation

import numpy as np
from scipy.constants import c

import i10simulation
import i10controls
import i10buttons #temporary

class Straight(object):

    """
    The physics of the I10 straight.

    Takes currents and converts them to time dependent kicks.
    Takes layout of the straight, applies these kicks to electron
    beam and produces photon beams at the insertion devices.
    """

    BEAM_RIGIDITY = 3e9/c
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])

    def __init__(self):

        """Get layout of straight, initialise values of PVs and link them
        up to listen to the monitored PV values."""

        self.data = i10simulation.Layout('config.txt')
        self.switch_to_sim = False
        self.simbuttons = i10buttons.MagnetCoordinator() #temporary - to be done in a nicer way

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

        """Calculate time-varying strengths of kicker magnets."""

        kick = [[],[],[],[],[]]
        pv_monitors = i10controls.PvMonitors.get_instance()
        if self.switch_to_sim == False:
            kick = self.current_to_kick(pv_monitors.get_scales()) * np.array([ # have I got the physics right for the scales and offsets?
                   np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
                   2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
                   + 1]) * 0.5 + self.current_to_kick(pv_monitors.get_offsets())

        elif self.switch_to_sim == True:
            kick = self.current_to_kick(self.simbuttons.simulated_scales) * np.array([
                   np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
                   2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
                   + 1]) * 0.5 + self.current_to_kick(self.simbuttons.simulated_offsets)

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
        pv_monitors = i10controls.PvMonitors.get_instance()
        if self.switch_to_sim == False:
            self.strength_setup(self.current_to_kick(pv_monitors.get_scales())
                                * strength_values + self.current_to_kick(
                                pv_monitors.get_offsets()))
        elif self.switch_to_sim == True:
            self.strength_setup(self.current_to_kick(self.simbuttons.simulated_scales)
                                * strength_values + self.current_to_kick(
                                self.simbuttons.simulated_offsets))
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

