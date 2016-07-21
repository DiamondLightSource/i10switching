#!/usr/bin/env dls-python2.7
#i10straight
# Contains Straight
# Calls i10simulation

import numpy as np
from scipy.constants import c

import i10simulation


# Collect data on electron and photon beams at time t.
class Straight(object):
    BEAM_RIGIDITY = 3e9/c
    # Conversion values between current and tesla for the kickers.
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])
    CURRENTS = np.array([23.2610, 23.2145, 10.188844, 23.106842, 23.037771]) # eventually camonitor...
    FIELDS = CURRENTS*AMP_TO_TESLA

    def __init__(self):
        self.data = i10simulation.Layout('config.txt')
        self.currents_add = np.array([0, 0, 0, 0, 0])
        self.max_kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in self.FIELDS])

    def current_to_kick(self, current):
        field = current * self.AMP_TO_TESLA
        kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in field])
        return kick

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kick = self.max_kick * 0.5 * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
               2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.current_to_kick(self.currents_add)
        return kick

    def strength_setup(self, strength_values): # put underscore at start

        for kicker, strength in zip(self.data.kickers, strength_values):
            kicker.set_strength(strength)

    # Create e and p beams at time t
    def timestep(self, t):

        self.strength_setup(self.calculate_strengths(t))
        beams = self.data.send_electrons_through()
        e_beam = beams[0]
        p_beam = beams[1]

        return e_beam, p_beam # Returns pos and vel of electrons and photons.

    # Calculate p beams for fixed magnet strengths
    def p_beam_range(self, strength_values):

        self.strength_setup(self.max_kick * strength_values
                            + self.current_to_kick(self.currents_add))
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

    def p_beam_lim(self, currents):

        kick_limits = self.current_to_kick(currents)
        self.strength_setup(kick_limits)
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

