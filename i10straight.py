#!/usr/bin/env dls-python2.7
#i10straight
# Contains Straight
# Calls i10simulation

import numpy as np
from scipy.constants import c

import i10simulation
import i10controls

class Straight(object):

    """
    Convert currents applied to kickers to time dependent kicks,
    apply these kicks to electron beam and produce photon beams at the
    insertion devices.
    """

    BEAM_RIGIDITY = 3e9/c
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])
#    CURRENTS = np.array([23.2610, 23.2145, 10.188844, 23.106842, 23.037771]) # needed for sim mode??
#    FIELDS = CURRENTS*AMP_TO_TESLA

    def __init__(self):
        self.data = i10simulation.Layout('config.txt')
        self.currents_add = np.array([0, 0, 0, 0, 0]) # not currently used... will be needed for simulation mode

        i10controls.register_listener(self.get_offsets)
        i10controls.register_listener(self.get_scales)
        self.offsets = i10controls.arrays[i10controls.ARRAYS.OFFSETS]
        self.scales = i10controls.arrays[i10controls.ARRAYS.SCALES]

    def get_offsets(self, key, index):

        """Gets magnet offsets from i10controls; 
        if an offset changes it is updated."""

        if key == i10controls.ARRAYS.OFFSETS:
            self.offsets[index] = i10controls.arrays[key][index]

    def get_scales(self, key, index):

        """Gets magnet scales from i10controls; 
        if a scale changes it is updated."""

        if key == i10controls.ARRAYS.SCALES:
            self.scales[index] = i10controls.arrays[key][index]

    def current_to_kick(self, current):

        """Convert currents (Amps) to fields (Tesla) and then to kick
        strength."""

        field = current * self.AMP_TO_TESLA
        kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in field])
        return kick

    def calculate_strengths(self, t):

        """Calculate time-varying strengths of kicker magnets."""

        kick = self.current_to_kick(self.scales) * 0.5 * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
               2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.current_to_kick(self.offsets)

        return kick

    def strength_setup(self, strength_values): # put underscore at start

        """Apply strengths to kickers."""

        for kicker, strength in zip(self.data.kickers, strength_values):
            kicker.set_strength(strength)

    def timestep(self, t):

        """Return positions and velocities of electron and photon beams at
        time t."""

        self.strength_setup(self.calculate_strengths(t))
        beams = self.data.send_electrons_through()
        e_beam = beams[0]
        p_beam = beams[1]

        return e_beam, p_beam

    def p_beam_range(self, strength_values):

        """Calculate beams defining maximum range through which the
        photon beams sweep during a cycle."""

        self.strength_setup(self.current_to_kick(self.scales) * strength_values
                            + self.current_to_kick(self.offsets))
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

    def p_beam_lim(self, currents):

        """Calculate the photon beam produced by magnets at their maximum
        strength settings."""

        kick_limits = self.current_to_kick(currents)
        self.strength_setup(kick_limits)
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

