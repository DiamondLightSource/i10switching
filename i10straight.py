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
    insertion devices. Controls the pvs for both the beam itself and the
    simulation.
    """

    BEAM_RIGIDITY = 3e9/c
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])

    def __init__(self):

        self.data = i10simulation.Layout('config.txt')

        self.switch_to_sim = False

        self.controls = i10controls.Controls()

        self.controls.register_listener(self.get_offsets)
        self.controls.register_listener(self.get_scales)
        self.controls.register_listener(self.get_setscales)
        # should these be in here or elsewhere?
        self.controls.register_listener(self.get_imin)
        self.controls.register_listener(self.get_imax)
        self.controls.register_listener(self.get_errors)

        self.offsets = self.controls.arrays[self.controls.ARRAYS.OFFSETS]
        self.scales = self.controls.arrays[self.controls.ARRAYS.SCALES]
        self.set_scales = self.controls.arrays[self.controls.ARRAYS.SET_SCALES]

        self.imin = self.controls.arrays[self.controls.ARRAYS.IMIN]
        self.imax = self.controls.arrays[self.controls.ARRAYS.IMAX]
        self.errors = self.controls.arrays[self.controls.ARRAYS.ERRORS]

        self.simulated_offsets = self.controls.arrays[self.controls.ARRAYS.OFFSETS]
        self.simulated_scales = self.controls.arrays[self.controls.ARRAYS.SCALES]

    def get_offsets(self, key, index):

        """
        Gets magnet offsets from i10controls; 
        if an offset changes it is updated.
        """

        if key == self.controls.ARRAYS.OFFSETS:
            self.offsets[index] = self.controls.arrays[key][index]

    def get_scales(self, key, index):

        """
        Gets scaling pv (WFSCA) from i10controls; 
        if a scale changes it is updated.
        """

        if key == self.controls.ARRAYS.SCALES:
            self.scales[index] = self.controls.arrays[key][index]

    def get_setscales(self, key, index):

        """
        Gets other scaling pv (SETWFSCA) from i10controls; 
        if a scale changes it is updated.
        """

        if key == self.controls.ARRAYS.SET_SCALES:
            self.set_scales[index] = self.controls.arrays[key][index]

    def get_imin(self, key, index):

        if key == self.controls.ARRAYS.IMIN:
            self.imin[index] = self.controls.arrays[key][index]

    def get_imax(self, key, index):

        if key == self.controls.ARRAYS.IMAX:
            self.imax[index] = self.controls.arrays[key][index]

    def get_errors(self, key, index):

        if key == self.controls.ARRAYS.ERRORS:
            self.errors[index] = self.controls.arrays[key][index]

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
        if self.switch_to_sim == False:
            kick = self.current_to_kick(self.scales) * np.array([ # have I got the physics right for the scales and offsets?
                   np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
                   2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
                   + 1]) * 0.5 + self.current_to_kick(self.offsets)

        elif self.switch_to_sim == True:
            kick = self.current_to_kick(self.simulated_scales) * np.array([
                   np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
                   2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
                   + 1]) * 0.5 + self.current_to_kick(self.simulated_offsets)

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
        beams = self.data.send_electrons_through()
        e_beam = beams[0]
        p_beam = beams[1]

        return e_beam, p_beam

    def p_beam_range(self, strength_values):

        """
        Calculate beams defining maximum range through which the
        photon beams sweep during a cycle.
        """

        if self.switch_to_sim == False:
            self.strength_setup(self.current_to_kick(self.scales)
                                * strength_values + self.current_to_kick(
                                self.offsets))
        elif self.switch_to_sim == True:
            self.strength_setup(self.current_to_kick(self.simulated_scales)
                                * strength_values + self.current_to_kick(
                                self.simulated_offsets))
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

