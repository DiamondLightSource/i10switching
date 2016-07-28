#!/usr/bin/env dls-python2.7
#i10simulation
# Contains Element classes, Layout (which now includes 'send_electrons_through')

import numpy as np


class Element(object):

    """Define matrices to modify the electron beam vector."""

    def __init__(self, displacement):
        self.s = displacement

    def increment(self, e):
        return e

    def get_type(self):
        """
            The device name is the name of the class extending :class:`Element`

        Returns:
            str: Name of the element.
        """
        return type(self).__name__.lower()


class Detector(Element):
    """End of the straight where the sample is located."""
    pass

class Drift(Element):
    """Allow electron beam to move along path described by its beam vector."""

    def __init__(self, displacement, length=0):
        super(Drift, self).__init__(displacement)
        self.length = length

    def set_length(self, length):
        self.length = length

    def increment(self, e):
        drift = np.array([[1, self.length],
                          [0, 1]])
        return np.dot(drift, e)


class Kicker(Element):
    """Magnet responsible for deflecting the electron beam."""

    def __init__(self, displacement, kick=0):
        super(Kicker, self).__init__(displacement)
        self.set_strength(kick)

    def set_strength(self, kick):
        self.k = kick

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick


class InsertionDevice(Element):
    """Generates x-ray beam."""
    pass


# TODO Move Layout into a separate py file

# Assign locations of devices along the axis of the system.
class Layout(object):

    """
    Set up layout of the straight using the information in the
    configuration file.
    """

    def __init__(self, name):
        self.path = self._load(name)
        self.ids = self.get_elements('insertiondevice') #CHANGEEEE
        self.kickers = self.get_elements('kicker')
        self.detector = self.get_elements('detector')
        self.p_coord = [[self.ids[i].s, self.detector[0].s] for i in range(len(self.ids))]
        self.xaxis = [0]
        self.xaxis.extend([i.s for i in self.path
                      if i.get_type() != 'drift'])
        self.travel = [Drift(self.ids[i].s) for i in range(len(self.ids))]

    def _load(self, filename):

        """Load data from configuration file."""

        raw_data = [line.split() for line in open(filename)]
        element_classes = {cls(None).get_type(): cls
                           for cls in Element.__subclasses__()}
        path = [element_classes[x[0]](float(x[1])) for x in raw_data]

        """Set lengths of drifts."""

        for p in path:
            if p.get_type() == 'drift':
                p.set_length(path[path.index(p)+1].s - p.s)

        return path

    def get_elements(self, which):

        """Return list of elements of a particular type from the straight."""

        return [x for x in self.path if x.get_type() == which]

    # TODO: not a great name
    def send_electrons_through(self):

        """
        Send electron beam vector through straight to generate electron beam
        and photon beams, which are initialised at the two insertion devices.
        """

        e_vector = np.array([0, 0])
        e_beam = np.zeros((len(self.path), 2))
        p_vector = []

        for x in self.path:
            if x.get_type() != 'detector':
                e_vector = x.increment(e_vector)
                e_beam[self.path.index(x)+1] = e_vector
            if x.get_type() == 'insertiondevice': #CHANGEEEEEE
                p_vector.append(e_vector.tolist())

        p_beam = self.create_photon_beam(p_vector)

        return e_beam, p_beam

    def create_photon_beam(self, vector):

        """Take initialised photon beams and extend them to the detector."""

        for i in range(len(self.ids)):
            self.travel[i].set_length(self.p_coord[i][1]
                                      - self.p_coord[i][0])
            vector[i].extend(self.travel[i].increment(vector[i]))

        return vector

