# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import cothread
from cothread.catools import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os


# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.


class Drift(object):


    def __init__(self, step=0, where=0):
        self.step = step
        self.where = where

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'drift'


class Kicker(object):


    def __init__(self, k=0, where=0):
        self.k = k
        self.where = where

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'kicker'


class InsertionDevice(object):


    def __init__(self, where=0):
        self.where = where

    def increment(self, e):
        return e

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'id'


# Assign the values of constants in the system:
# distances between devices and strength of 3rd kicker.

class Constants(object):

    LENGTHS = [2,2,4,4,4,4,2,20]


# Assign locations of devices along the axis of the system.

class Location(object):


    def __init__(self):
        self.lengths = Constants().LENGTHS
        self.path = [
                    Drift(),Kicker(),
                    Drift(),Kicker(),
                    Drift(),InsertionDevice(),
                    Drift(),Kicker(),
                    Drift(),InsertionDevice(),
                    Drift(),Kicker(),
                    Drift(),Kicker(),
                    Drift()
                    ]

    def positions(self):
        
        pos = [0]
        pos.extend(np.cumsum(self.lengths))

        return pos

    def locate_devices(self):

        kicker_pos = []
        id_pos = []
        devices = [x for x in self.path if x.get_type() != 'drift']
        for device, where in zip(devices, self.positions()[1:]):
            device.set_position(where)
        for device in devices:
            if device.get_type() == 'kicker':
                kicker_pos.append(device.coordinate())
            elif device.get_type() == 'id':
                id_pos.append(device.coordinate())

        return kicker_pos, id_pos
    
    def locate_detector(self):
        return self.positions()[8]

    def locate_photonbeam(self):
        return [[self.locate_devices()[1][0], self.locate_detector()],
                [self.locate_devices()[1][1], self.locate_detector()]]

    def get_elements(self, which):
        return [x for x in self.path if x.get_type() == which]


# Collect data on electron and photon beams at time t.
class Magnet_strengths(object):


    def __init__(self, k3=1):
        self.numbers = Constants()
        self.locate = Location()
        self.k3 = k3

    def step_k3(self, shift):
        self.k3 += shift

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kicker_pos = self.locate.locate_devices()[0]
        d12 = float(kicker_pos[1] - kicker_pos[0])/float(kicker_pos[2] - kicker_pos[1])
        d34 = float(kicker_pos[3] - kicker_pos[2])/float(kicker_pos[4] - kicker_pos[3])
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 
        graphscale = 0.5
        kicker3 = self.k3
        kick = graphscale * max_kick * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               kicker3, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1])

        return kick


class Collect_data(object):


    def __init__(self):

        self.numbers = Constants()
        self.locate = Location()
        self.path = self.locate.path
#        self.e_vector = [[0,0]]
#        self.p_vector = []
    #PUT THIS IN A FUNCTION? OR CLASS?
    # Set drift distances (time independent).
        for drift, distance in zip(self.locate.get_elements('drift'), self.numbers.LENGTHS):
            drift.set_length(distance)
        self.magnets = Magnet_strengths()
    
    # Send electron vector through chicane magnets at time t.
    def timestep(self,t):
    
        # Initialise electron beam position and velocity
        e_beam = np.array([0,0])
        e_vector = [[0,0]]
    
        # Initialise photon beam position and velocity
        p_vector = []

        # Calculate positions of electron beam and photon beam relative to main axis.
        for kicker, strength in zip(self.locate.get_elements('kicker'), self.magnets.calculate_strengths(t)):
             kicker.set_strength(strength)

        for p in self.path:
            e_beam = p.increment(e_beam)
            device = p.get_type()
            e_vector.append(e_beam.tolist())
            if device == 'id':
                p_vector.append(e_beam.tolist())  # Electron vector passes through insertion device, photon vector created

        return e_vector, p_vector # Returns positions and velocities of electrons and photons.
    
    
    # Extract electron beam positions for plotting.
    def e_plot(self, e_beam):
    
        e_positions = np.array(e_beam)[:,0].tolist()
        # Remove duplicates in data.
        for i in range(len(self.locate.get_elements('drift'))):
            if e_positions[i] == e_positions[i+1]:
                e_positions.pop(i+1)
        
        return e_positions
    
    # Allow the two photon vectors to drift over large distance 
    # and add the vector for new position and velocity to 
    # original vector to create beam for plotting.
    def p_plot(self, p_beam):
        
        travel = [Drift(),Drift()]
        p_pos = self.locate.locate_photonbeam()
        for i in range(2):
            travel[i].set_length(p_pos[i][1]-p_pos[i][0])
            p_beam[i].extend(travel[i].increment(p_beam[i]))
    
        p_positions = np.array(p_beam)[:,[0,2]]
    
        return p_positions


####################
## Graph plotting ##
####################

class Plot(FigureCanvas):


    def __init__(self):

        self.lengths = Constants().LENGTHS
        self.locate = Location()
        self.information = Collect_data()
        self.fig = plt.figure()
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig_setup()
        self.beams = self.data_setup()

        # Create animations
        self.anim = animation.FuncAnimation(self.fig, self.animate, 
                    init_func=self.init_data, frames=1000, interval=20, blit=True)
        # Plot positions of kickers and IDs.
        for i in self.locate.locate_devices()[0]:
            self.fig_setup().axvline(x=i, color='k', linestyle='dashed')
        for i in self.locate.locate_devices()[1]:
            self.fig_setup().axvline(x=i, color='r', linestyle='dashed')

    def fig_setup(self):

        ax1 = self.fig.add_subplot(1, 1, 1)
        ax1.set_xlim(0, sum(self.lengths))
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-2, 5)

        return ax1

    def data_setup(self):

        beams = [
                self.axes.plot([], [])[0], 
                self.axes.plot([], [], 'r')[0], 
                self.axes.plot([], [], 'r')[0], 
                ]

        return beams

    def init_data(self):

        for line in self.beams:
            line.set_data([], [])

        return self.beams

    # Animation function
    def animate(self, t):
#        t = t*4 # This gets it to one cycle per second.

        # Obtain data for plotting.
        data = self.information.timestep(t)
        e_data = self.information.e_plot(data[0])
        p_data = self.information.p_plot(data[1]) ############## Tried to change this but failed - new attempt needed
        detector_data = p_data[:,1].tolist()

        beams = self.init_data()
        beams[0].set_data(self.locate.positions(), e_data)
        for line, x, y in zip([beams[1],beams[2]], self.locate.locate_photonbeam(), p_data):
            line.set_data(x,y)

        return beams


############################

# Initial attempt at adding GUI to control the simulation.

UI_FILENAME = 'i10chicgui.ui'


class Control(QMainWindow):


    def __init__ (self):
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)

        self.ui.graph = Plot()
        self.ui.matplotlib_layout.addWidget(self.ui.graph)

        self.ui.kplusButton.clicked.connect(lambda: self.k3(0.1))
        self.ui.kminusButton.clicked.connect(lambda: self.k3(-0.1))
        self.ui.quitButton.clicked.connect(sys.exit)

    def k3(self, n):
        self.ui.graph.information.magnets.step_k3(n)

def main():
    cothread.iqt()
    test_ui = Control()
    test_ui.ui.show()
    cothread.WaitForQuit()

if __name__ == '__main__':
    main()


