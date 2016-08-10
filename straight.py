#!/usr/bin/env dls-python2.7
# straight.py
# Contains RealModeController, SimModeController, Straight
# Calls simulation, controls

import numpy as np
import scipy.constants

import simulation
import controls


class RealModeController(object):

    """
    Control simulation using the camonitored offsets/scales from PvMonitors.
    """

    def __init__(self):
        self.pvm = controls.PvMonitors.get_instance()
        self.pvm.register_straight_listener(self.update)
        self.straights = []

    def update(self, key, _):
        """Update scales and offsets whenever they change."""
        if key == controls.Arrays.SCALES:
            for straight in self.straights:
                straight.set_scales(self.pvm.get_scales())

        elif key == controls.Arrays.OFFSETS:
            for straight in self.straights:
                straight.set_offsets(self.pvm.get_offsets())

    def register_straight(self, straight):
        """Register the straight with the controller linked to PVs."""
        self.straights.append(straight)
        self.update(controls.Arrays.SCALES, 0)
        self.update(controls.Arrays.OFFSETS, 0)

    def deregister_straight(self, straight):
        self.straights.remove(straight)


class SimModeController(object):

    """Control simulation using the simulated values from SimWriter."""

    def __init__(self):

        self.straights = []
        self.offsets = controls.PvMonitors.get_instance().get_offsets()
        self.scales =  controls.PvMonitors.get_instance().get_scales()

    def update_sim(self, key, values):
        """Update simulated scales and offsets whenever they change."""
        if key == controls.Arrays.SCALES:
            self.scales = values
            self.update_scales()

        if key == controls.Arrays.OFFSETS:
            self.offsets = values
            self.update_offsets()

    def register_straight(self, straight):
        """Register the straight with controller linked to the simulation."""
        self.straights.append(straight)
        self.update_sim(controls.Arrays.SCALES, self.scales)
        self.update_sim(controls.Arrays.OFFSETS, self.offsets)

    def deregister_straight(self, straight):
        self.straights.remove(straight)

    def update_scales(self):
        for straight in self.straights:
            straight.set_scales(self.scales)

    def update_offsets(self):
        for straight in self.straights:
            straight.set_offsets(self.offsets)


class Straight(object):

    """
    The physics of the I10 straight.

    Takes currents and converts them to time dependent kicks.
    Takes layout of the straight, applies these kicks to electron
    beam and produces photon beams at the insertion devices.
    """

    BEAM_RIGIDITY = 3e9/scipy.constants.c
    AMP_TO_TESLA = np.array([0.034796/23, -0.044809/23, 0.011786/12,
                            -0.045012/23,  0.035174/23])

    def __init__(self):
        """Get layout of straight, initialise values of PVs and link them
        up to listen to the monitored PV values."""
        self.data = simulation.Layout('config.txt')
        self.scales = controls.PvMonitors.get_instance().get_scales()
        self.offsets = controls.PvMonitors.get_instance().get_offsets()

    def set_scales(self, scales):
        self.scales = scales

    def set_offsets(self, offsets):
        self.offsets = offsets

    def amps_to_radians(self, current):
        """Convert currents (Amps) to fields (Tesla) to kick strength (rads)."""
        field = current * self.AMP_TO_TESLA
        kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY))
                                  for x in field])
        return kick

    def calculate_strengths(self, t):
        """
        Calculate time-varying strengths of kicker magnets.
            Args:
                t (int): time in sec
            Returns:
                new kicker strengths (array of 5 by 1)
        """
        waves = np.array([
                np.sin(t * np.pi / 100) + 1,
                np.sin(t * np.pi / 100) + 1,
                2,
                -np.sin(t * np.pi / 100) + 1,
                -np.sin(t * np.pi / 100) + 1])
        return self.amps_to_radians(self.scales * waves + self.offsets)

        kick = self.amps_to_radians(
                0.5 * self.scales *
                + self.offsets)
        return kick

    def strength_setup(self, strength_values): # put underscore at start
        """Apply strengths to kickers."""
        for kicker, strength in zip(self.data.kickers, strength_values):
            kicker.set_strength(strength)

    def step(self, t):
        """
        Create electron and photon beams.

        Return positions and velocities of electron and photon beams at
        positions along the straight at time t.
        """
        self.strength_setup(self.calculate_strengths(t))
        e_beam, p_beam = self.data.generate_beams()

        return e_beam, p_beam

    def p_beam_range(self, strength_values):
        """
        Edges of photon beam range.

        Calculate beams defining maximum range through which the
        photon beams sweep during a cycle.
        """
        self.strength_setup(self.amps_to_radians(
            self.scales * strength_values + self.offsets))

        p_beam = self.data.generate_beams()[1]

        return p_beam

    def p_beam_lim(self, currents):
        """
        Limits on the photon beams due to magnet strengths.

        Calculate the photon beam produced by magnets at their maximum
        strength settings.
        """
        kick_limits = self.amps_to_radians(currents)
        self.strength_setup(kick_limits)
        p_beam = self.data.generate_beams()[1]

        return p_beam
