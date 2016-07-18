#i10straight
# Contains ButtonData, MagnetStrengths, CollectData
# Calls i10simulation

import numpy as np
from scipy.constants import c

import i10simulation

## will eventually be got from pvs
class ButtonData(object):
    STEP_K3 = [0, 0, 0.1, 0, 0]
    BUMP_LEFT = [0.1, -0.1, 0.05, 0, 0]
    BUMP_RIGHT = [0, 0, 0.05, -0.1, 0.1]
    BPM1 = [0.01, 0.01, 0, -0.01, -0.01]
    BPM2 = [-0.01, -0.01, 0, 0.01, 0.01]
    SCALE = [0.01, 0.01, 0, 0.01, 0.01]

    SHIFT = [STEP_K3, BUMP_LEFT, BUMP_RIGHT, BPM1, BPM2, SCALE]


# Collect data on electron and photon beams at time t.
class MagnetStrengths(object):
    BEAM_RIGIDITY = 3e9/c
    # Conversion values between current and tesla for the kickers.
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12,
                             0.045012/23, 0.035174/23])
    CURRENTS = np.array([23.261, 23.2145, 10.188844, 23.106842, 23.037771])
    FIELDS = CURRENTS*AMP_TO_TESLA

    def __init__(self):
        self.kick_add = np.array([0, 0, 0, 0, 0])
        self.max_kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in self.FIELDS])

    # Define alterations to the kickers.
    def buttons(self, factor, button):

        self.kick_add = self.kick_add+factor*np.array(ButtonData.SHIFT[button])

    def reset(self):

        self.kick_add = np.array([0, 0, 0, 0, 0])

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kick = self.max_kick * (np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1),
               2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.kick_add)

        return kick


class CollectData(object):


    def __init__(self):

        self.data = i10simulation.Layout()
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

        self.strength_setup(self.magnets.max_kick
                            * (strength_values + self.magnets.kick_add))
        p_beam = self.data.send_electrons_through()[1]

        return p_beam



