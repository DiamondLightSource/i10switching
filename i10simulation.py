#i10simulation
# Contains Element classes, Layout (which now includes 'send_electrons_through')

import numpy as np

# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.

class Element(object):


    def __init__(self, s):
        self.where = s


class Detector(Element):

    def __init__(self, s):
        self.s = s

    def get_type(self):
        return 'detector'


class Drift(Element):


    def __init__(self, s, step=0):
        self.step = step
        self.s = s

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1, self.step],
                          [0, 1]])
        return np.dot(drift, e)

    def get_type(self):
        return 'drift'


class Kicker(Element):


    def __init__(self, s, k=0):
        self.k = k
        self.s = s

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def get_type(self):
        return 'kicker'


class InsertionDevice(Element):


    def __init__(self, s):
        self.s = s

    def increment(self, e):
        return e

    def get_type(self):
        return 'id'


# Assign locations of devices along the axis of the system.
class Layout(object):

    def __init__(self, name):
        self.NAME = name # best way to call it?
        self.path = self.load()
        self.ids = self.get_elements('id') # should these REALLY be here?
        self.kickers = self.get_elements('kicker')
        self.detector = self.get_elements('detector')
        self.p_coord = [[self.ids[0].s,
                         self.detector[0].s],
                        [self.ids[1].s,
                         self.detector[0].s]]
        self.xaxis = [0]
        self.xaxis.extend([i.s for i in self.path
                      if i.get_type() != 'drift'])
        self.travel = [Drift(self.ids[0].s),
                       Drift(self.ids[1].s)]

    def load(self):

        raw_data = [line.split() for line in open(self.NAME)]
        element_classes = {cls(None).get_type(): cls
                           for cls in Element.__subclasses__()}
        path = [element_classes[x[0]](float(x[1])) for x in raw_data]

        # Set drift lengths
        for p in path:
            if p.get_type() == 'drift':
                p.set_length(path[path.index(p)+1].s - p.s)

        return path

    def get_elements(self, which):
        return [x for x in self.path if x.get_type() == which]

    def send_electrons_through(self):

        e_vector = np.array([0, 0])
        e_beam = np.zeros((len(self.path), 2))
        p_vector = []

        # Send e_vector through system and create electron and photon beams
        for x in self.path:
            if x.get_type() != 'detector':
                e_vector = x.increment(e_vector)
                e_beam[self.path.index(x)+1] = e_vector
            if x.get_type() == 'id':
                p_vector.append(e_vector.tolist())
        p_beam = self.create_photon_beam(p_vector)

        return e_beam, p_beam

    def create_photon_beam(self, vector):

        for i in range(2):
            self.travel[i].set_length(self.p_coord[i][1]
                                      - self.p_coord[i][0])
            vector[i].extend(self.travel[i].increment(vector[i]))

        return vector

