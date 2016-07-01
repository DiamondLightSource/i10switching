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
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os

# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.


# Inherit from something like this
class Element(object): # do I need to call an instance of where up here?


    def __init__(self):
        self.where  # or can I just do this?

    def set_position(self, where):
        self.where = where


class Drift(Element):


    def __init__(self, step=0):
        self.step = step

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def get_type(self):
        return 'drift'


class Kicker(Element):


    def __init__(self, k=0):
        self.k = k

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def get_type(self):
        return 'kicker'


class InsertionDevice(Element):


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def get_type(self):
        return 'id'


class Constants(object):

    LENGTHS = [2,2,4,4,4,4,2,20]



# Assign locations of devices along the axis of the system.

class Location(object):


    def __init__(self):

        self.path = self.load_data()[1] # MOVE THIS - probably not ideal
# HOW ON EARTH AM I SUPPOSED TO GET ALL THE LAYOUT STUFF INTO THE CONFIG FILE? LAYOUT STUFF IS CURRENTLY DEPENDENT ON THE DRIFT ETC CLASSES AND THE CONFIG FILE IS A TXT FILE SO I CAN'T PUT COMMANDS IN THERE......

# PARTIAL USE OF CONFIG FILE WITH PATH AND LENGTHS IN IT
    def load_data(self):
        #d = {key: value for (key, value) in iterable}
#        element_classes = {cls.get_type(): cls for cls in Element.__subclasses__()}


        raw_data = [line.strip().split() for line in open('i10chicconfig.txt')]

#        elements = {eval(el).get_type(): eval(el) for el in raw_data[1][1:]} # key not unique for different kickers etc
        lengths = []
        for i in raw_data[0][1:]:
            lengths.append(eval(i))
        path = []
        for i in raw_data[1][1:]:
            path.append(eval(i))

        return lengths, path # not currently using lengths at all...


    def positions(self):
        
        pos = [0]
        pos.extend(np.cumsum(Constants.LENGTHS))

        return pos

    def locate_devices(self):

        kicker_pos = []
        id_pos = []
        devices = [x for x in self.path if x.get_type() != 'drift']
        for device, where in zip(devices, self.positions()[1:]):
            device.set_position(where)
        for device in devices:
            if device.get_type() == 'kicker':
                kicker_pos.append(device.where)
            elif device.get_type() == 'id':
                id_pos.append(device.where)

        return kicker_pos, id_pos
    
    def locate_detector(self):
        return self.positions()[8]

    def locate_photonbeam(self):
        return [[self.locate_devices()[1][0], self.locate_detector()],
                [self.locate_devices()[1][1], self.locate_detector()]]

    def get_elements(self, which):
        return [x for x in self.path if x.get_type() == which]


# Collect data on electron and photon beams at time t.
class MagnetStrengths(object):


    def __init__(self, k3=1):
        self.locate = Location()
        self.k3 = k3
        self.k1 = 0
        self.k2 = 0
        self.k4 = 0
        self.k5 = 0

    def step_k3(self, shift):
        self.k3 += shift

    def bump_left(self,shift):
        print 'bump!' # set things up ready to implement bump

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kicker_pos = self.locate.locate_devices()[0]
        d12 = float(kicker_pos[1] - kicker_pos[0])/float(kicker_pos[2] - kicker_pos[1])
        d34 = float(kicker_pos[3] - kicker_pos[2])/float(kicker_pos[4] - kicker_pos[3])
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) + np.array([self.k1, self.k2, 0, self.k4, self.k5]) # to be sorted so that the appropriate bumps can be added
        graphscale = 0.5
        kicker3 = self.k3
        kick = graphscale * max_kick * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               kicker3, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1])

        return kick


class CollectData(object):


    def __init__(self):

        self.locate = Location()
        self.path = self.locate.path
    #PUT THIS IN A FUNCTION? OR CLASS? DON'T KNOW HOW TO GET IT TO WORK IF I MOVE IT ANYWHERE ELSE
    # Set drift distances (time independent).
        for drift, distance in zip(self.locate.get_elements('drift'), Constants.LENGTHS):
            drift.set_length(distance)
        self.magnets = MagnetStrengths()

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

        travel = [Drift(),Drift()]
        p_pos = self.locate.locate_photonbeam()
        for i in range(2):
            travel[i].set_length(p_pos[i][1]-p_pos[i][0])
            p_vector[i].extend(travel[i].increment(p_vector[i]))

        return e_vector, p_vector # Returns positions and velocities of electrons and photons.


####################
## Graph plotting ##
####################

class Plot(FigureCanvas):


    def __init__(self):

        self.locate = Location()
        self.information = CollectData()
        self.fig = plt.figure()
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig_setup()
        self.beams = self.data_setup()
        self.colourin = [[],[]]

        # Create animations
        self.anim = animation.FuncAnimation(self.fig, self.animate, 
                    init_func=self.init_data, frames=1000, interval=20, blit=True)
#        self.animate(0)

        # Plot positions of kickers and IDs.
        for i in self.locate.locate_devices()[0]: # this should be in init function
            self.axes[0].axvline(x=i, color='k', linestyle='dashed')
        for i in self.locate.locate_devices()[1]:
            self.axes[0].axvline(x=i, color='r', linestyle='dashed')

# THIS NEEDS UPDATING AFTER EDITS MADE TO CODE
#        for i in range(2):
#            self.colourin[i] = self.information.p_plot(self.information.timestep(50 + 100*i)[1])[i] # very dodgy - want max and min positions (which happen to be 50 and 150) and want them to update when k3 changes
#            self.axes[0].fill_between(self.locate.locate_photonbeam()[i],0,self.colourin[i], facecolor='yellow', alpha=0.2)



    def fig_setup(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_xlim(0, sum(Constants.LENGTHS))
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-2, 5)
        ax2 = self.fig.add_subplot(2, 1, 2)

        return ax1, ax2

    def data_setup(self):

        beams = [
                self.axes[0].plot([], [])[0], 
                self.axes[0].plot([], [], 'r')[0], 
                self.axes[0].plot([], [], 'r')[0]
                ]

        return beams

    def init_data(self):

        for line in self.beams:
            line.set_data([], [])

        return self.beams

    
    # Extract electron and photon beam positions for plotting.
    def beam_plot(self, t):
    
        e_positions = np.array(self.information.timestep(t)[0])[:,0].tolist()
        # Remove duplicates in data.
        for i in range(len(self.locate.get_elements('drift'))):
            if e_positions[i] == e_positions[i+1]:
                e_positions.pop(i+1)

        p_positions = np.array(self.information.timestep(t)[1])[:,[0,2]]
        
        return e_positions, p_positions

    # Animation function
    def animate(self, t):
#        t = t*4 # This gets it to one cycle per second.

        # Obtain data for plotting.
        data = self.beam_plot(t)
        e_data = data[0]
        p_data = data[1]

        beams = self.init_data()
        beams[0].set_data(self.locate.positions(), e_data)
        for line, x, y in zip([beams[1],beams[2]], self.locate.locate_photonbeam(), p_data):
            line.set_data(x,y)


        return beams


############################

# Initial attempt at adding GUI to control the simulation.

UI_FILENAME = 'i10chicgui.ui'


class Gui(QMainWindow):


    def __init__ (self):
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.ui.graph = Plot()
        self.ui.matplotlib_layout.addWidget(self.ui.graph)
        self.ui.kplusButton.clicked.connect(lambda: self.k3(0.1))
        self.ui.kminusButton.clicked.connect(lambda: self.k3(-0.1))
        self.ui.bumpleftplusButton.clicked.connect(lambda: self.bump_left(0.1))
        self.ui.bumpleftminusButton.clicked.connect(lambda: self.bump_left(-0.1))


        self.toolbar = NavigationToolbar(FigureCanvas(Plot().fig), 
                        self.ui.centralwidget, coordinates=True) # doesn't currently connect...
        self.ui.matplotlib_layout.addWidget(self.toolbar)
        

        self.ui.quitButton.clicked.connect(sys.exit)

    def k3(self, n):
        self.ui.graph.information.magnets.step_k3(n)

    def bump_left(self, n):
        self.ui.graph.information.magnets.bump_left(n)

def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


