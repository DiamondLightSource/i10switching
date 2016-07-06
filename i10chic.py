# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

#import dls_packages
from pkg_resources import require
require('cothread==2.10')
require('scipy==0.10.1')
require('matplotlib==1.3.1')
require('numpy==1.11.1') # is this right?
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
from PyQt4.QtGui import QMainWindow
import os
import scipy.integrate as integ

# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.

class Element(object):


    def __init__(self):
        self.where

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


# Assign locations of devices along the axis of the system.

class Layout(object):


    def __init__(self):

        self.path = self.load_data()[1] # MOVE THIS - probably not ideal
        self.lengths = self.load_data()[0]

# PARTIAL USE OF CONFIG FILE WITH PATH AND LENGTHS IN IT
    def load_data(self):
        #d = {key: value for (key, value) in iterable}
#        element_classes = {cls.get_type(): cls for cls in Element.__subclasses__()}
#        elements = {eval(el).get_type(): eval(el) for el in raw_data[1][1:]} # key not unique for different kickers etc


        raw_data = [line.strip().split() for line in open('i10chicconfig.txt')]

        lengths = []
        for i in raw_data[0][1:]:
            lengths.append(eval(i))
        path = []
        for i in raw_data[1][1:]:
            path.append(eval(i))

        button_data = [[],[],[],[],[]]
        for i in range(2,7):
            for j in raw_data[i][1:]:
                button_data[i-2].append(eval(j))

        max_kick = []
        for i in raw_data[7][1:]:
            max_kick.append(eval(i))

        return lengths, path, button_data, max_kick # not currently using max_kick at all...

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
        self.locate = Layout()
        self.button_data = self.locate.load_data()[2]
        self.k3 = k3
        self.kick_add = np.array([0,0,0,0,0])
        self.limit = self.locate.load_data()[3]

    # Define alterations to the kickers.
    def step_k3(self, factor):

        self.kick_add = self.kick_add + factor*np.array(self.button_data[0])

    def bump_left(self, factor):

        self.kick_add = self.kick_add + factor*np.array(self.button_data[1])

    def bump_right(self, factor):

        self.kick_add = self.kick_add + factor*np.array(self.button_data[2])

    def bpm1(self, factor):

        self.kick_add = self.kick_add + factor*np.array(self.button_data[3])

    def bpm2(self, factor):

        self.kick_add = self.kick_add + factor*np.array(self.button_data[4])

    def reset(self):

        self.kick_add = np.array([0,0,0,0,0])

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kicker_pos = self.locate.locate_devices()[0]
        d12 = float(kicker_pos[1] - kicker_pos[0])/float(kicker_pos[2] - kicker_pos[1])
        d34 = float(kicker_pos[3] - kicker_pos[2])/float(kicker_pos[4] - kicker_pos[3])
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 
        graphscale = 0.5
        kicker3 = self.k3
        kick = graphscale * max_kick * (np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               kicker3, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.kick_add)
        kick_limit = graphscale * max_kick * self.limit

        return kick, kick_limit

class CollectData(object):


    def __init__(self):

        self.locate = Layout()
        self.path = self.locate.path #WHYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
    #PUT THIS IN A FUNCTION? OR CLASS? DON'T KNOW HOW TO GET IT TO WORK IF I MOVE IT ANYWHERE ELSE
    # Set drift distances (time independent).
        for drift, distance in zip(self.locate.get_elements('drift'), 
                               self.locate.lengths):
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
        for kicker, strength in zip(self.locate.get_elements('kicker'), 
                                self.magnets.calculate_strengths(t)[0]):
             kicker.set_strength(strength)

        for p in self.path:
            e_beam = p.increment(e_beam)
            device = p.get_type()
            e_vector.append(e_beam.tolist())
            if device == 'id':
                p_vector.append(e_beam.tolist())

        travel = [Drift(),Drift()]
        p_pos = self.locate.locate_photonbeam()
        for i in range(2):
            travel[i].set_length(p_pos[i][1]-p_pos[i][0])
            p_vector[i].extend(travel[i].increment(p_vector[i]))

        return e_vector, p_vector # Returns pos and vel of electrons and photons.


####################
## Graph plotting ##
####################

class Plot(FigureCanvas):


    def __init__(self):

        self.locate = Layout()
        self.information = CollectData()
        self.fig = plt.figure()
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig_setup()
        self.beams = self.data_setup()

    def fig_setup(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_xlim(0, sum(self.locate.lengths))
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-2, 8)
        ax2 = self.fig.add_subplot(2, 1, 2)
        ax2.get_xaxis().set_visible(False)
        ax2.get_yaxis().set_visible(False)

        return ax1, ax2

    def data_setup(self):

        beams = [
                self.axes[0].plot([], [])[0], 
                self.axes[0].plot([], [], 'r')[0], 
                self.axes[0].plot([], [], 'r')[0]]

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
        for line, x, y in zip([beams[1],beams[2]], 
                          self.locate.locate_photonbeam(), p_data):
            line.set_data(x,y)

        return beams

    def show_plot(self):

        # Plot positions of kickers and IDs.
        for i in self.locate.locate_devices()[0]:
            self.axes[0].axvline(x=i, color='k', linestyle='dashed')
        for i in self.locate.locate_devices()[1]:
            self.axes[0].axvline(x=i, color='r', linestyle='dashed')

        xcolour = (self.locate.locate_devices()[0][2],self.locate.locate_detector())
        ycolour = (0,self.beam_plot(150)[1][1][1])
        ycolour2 = (0,self.beam_plot(50)[1][0][1])
        self.axes[0].fill_between( xcolour, ycolour, ycolour2, facecolor='yellow', alpha=0.2) # messy but works

        # Create animations
        self.anim = animation.FuncAnimation(self.fig, self.animate, 
                    init_func=self.init_data, frames=1000, interval=20, blit=True)

    def gauss_plot(self):
        # Eventually to be live plot

        # Import data
        trigger = np.load('trigger.npy')[1200:6200]
        trace = np.load('diode.npy')[1200:6200]

        # Number of data points
        GRAPHRANGE = 5000
        WINDOW = GRAPHRANGE/2
        # Shift between edge of square wave and peak of Gaussian
        CENTRESHIFT = 25

        x = np.linspace(0, GRAPHRANGE, GRAPHRANGE)

        # Finds edges of square wave
        sqdiff = np.diff(trigger).tolist()
        edges = [sqdiff.index(max(sqdiff)), sqdiff.index(min(sqdiff))]

        # Overlay the two gaussians
        peak1 = np.array(trace[:WINDOW])
        peak2 = np.array(trace[WINDOW:])
        xwindow = np.linspace(-WINDOW/2, WINDOW/2, WINDOW)
        peak1shift = WINDOW/2 - edges[0] - CENTRESHIFT
        peak2shift = 3*WINDOW/2 - edges[1] - CENTRESHIFT
        self.axes[1].plot(xwindow + peak1shift,peak1, label=integ.simps(peak1))
        self.axes[1].plot(xwindow + peak2shift,peak2, label=integ.simps(peak2))
        self.axes[1].legend()


############################

# Initial attempt at adding GUI to control the simulation.

UI_FILENAME = 'i10chicgui.ui'


class Gui(QMainWindow):


    def __init__ (self):
        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)
        self.ui.graph = Plot()
        self.toolbar = NavigationToolbar(self.ui.graph, self)
        self.ui.matplotlib_layout.addWidget(self.ui.graph)
        self.ui.matplotlib_layout.addWidget(self.toolbar)

        self.ui.kplusButton.clicked.connect(lambda: self.k3(1))
        self.ui.kminusButton.clicked.connect(lambda: self.k3(-1))
        self.ui.bumpleftplusButton.clicked.connect(lambda: self.bump_left(1))
        self.ui.bumpleftminusButton.clicked.connect(lambda: self.bump_left(-1))
        self.ui.bumprightplusButton.clicked.connect(lambda: self.bump_right(1))
        self.ui.bumprightminusButton.clicked.connect(lambda: self.bump_right(-1))
        self.ui.bpm1plusButton.clicked.connect(lambda: self.bpm1(1))
        self.ui.bpm1minusButton.clicked.connect(lambda: self.bpm1(-1))
        self.ui.bpm2plusButton.clicked.connect(lambda: self.bpm2(1))
        self.ui.bpm2minusButton.clicked.connect(lambda: self.bpm2(-1))
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.graph.show_plot()
        self.ui.graph.gauss_plot()

    def k3(self, n):
        self.ui.graph.information.magnets.step_k3(n)

    def bump_left(self, n):
        self.ui.graph.information.magnets.bump_left(n)

    def bump_right(self, n):
        self.ui.graph.information.magnets.bump_right(n)

    def bpm1(self, n):
        self.ui.graph.information.magnets.bpm1(n)

    def bpm2(self, n):
        self.ui.graph.information.magnets.bpm2(n)

    def reset(self):
        self.ui.graph.information.magnets.reset()

def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


