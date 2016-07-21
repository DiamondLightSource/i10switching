#!/usr/bin/env dls-python2.7
#i10straight
# Contains ButtonData, MagnetStrengths, CollectData
# Calls i10simulation

import numpy as np
from scipy.constants import c

import i10simulation
import i10buttons

# Collect data on electron and photon beams at time t.
class MagnetStrengths(object):
    BEAM_RIGIDITY = 3e9/c
    # Conversion values between current and tesla for the kickers.
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])
    CURRENTS = np.array([23.2610, 23.2145, 10.188844, 23.106842, 23.037771])
    FIELDS = CURRENTS*AMP_TO_TESLA

    def __init__(self):
        self.fields_add = np.array([0, 0, 0, 0, 0])
        self.offset = np.array([0, 0, 0, 0, 0])
        self.max_kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in self.FIELDS])
        self.knobs = i10buttons.Knobs()


    # Define alterations to the kickers.
    def buttons(self, factor, button):

        self.fields_add = self.fields_add + (factor*np.array(
                          self.knobs.button_data[button])
                          *self.AMP_TO_TESLA*i10buttons.Knobs.jog_scale)
        self.offset = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in self.fields_add])

    def reconfigure(self, settings):

        self.fields_add = settings*self.AMP_TO_TESLA
        self.offset = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in self.fields_add])

    def reset(self):

        self.fields_add = np.array([0, 0, 0, 0, 0])
        self.offset = np.array([0, 0, 0, 0, 0])

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kick = self.max_kick * 0.5 * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
               2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.offset

        return kick


class CollectData(object):

    def __init__(self):

        self.data = i10simulation.Layout('config.txt')
        self.magnets = MagnetStrengths()

    def strength_setup(self, strength_values):

        for kicker, strength in zip(self.data.kickers, strength_values):
            kicker.set_strength(strength)

    # Create e and p beams at time t
    def timestep(self, t):

        self.strength_setup(self.magnets.calculate_strengths(t))
        beams = self.data.send_electrons_through()
        e_beam = beams[0]
        p_beam = beams[1]

        return e_beam, p_beam # Returns pos and vel of electrons and photons.

    # Calculate p beams for fixed magnet strengths
    def p_beam_range(self, strength_values):

        self.strength_setup(self.magnets.max_kick * strength_values
                            + self.magnets.offset)
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

    def p_beam_lim(self, currents):

        fields = currents * self.magnets.AMP_TO_TESLA
        kick_limits = np.array([2 * np.arcsin(x/(2*self.magnets.BEAM_RIGIDITY))
                                  for x in fields])
        self.strength_setup(kick_limits)
        p_beam = self.data.send_electrons_through()[1]

        return p_beam

