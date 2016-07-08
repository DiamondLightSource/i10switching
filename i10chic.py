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
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

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


class ButtonData(object):
        STEP_K3 = [0,0,0.1,0,0]
        BUMP_LEFT = [0.1,-0.1,0.05,0,0]
        BUMP_RIGHT = [0,0,0.05,-0.1,0.1]
        BPM1 = [0.01,0.01,0,-0.01,-0.01]
        BPM2 = [-0.01,-0.01,0,0.01,0.01]


# Assign locations of devices along the axis of the system.

class Layout(object):

    NAME = 'config.txt'

    def __init__(self):
        self.path = self.load()

    def load(self):

        raw_data = [line.split() for line in open(self.NAME)]
        element_classes = {cls(None).get_type(): cls for cls in Element.__subclasses__()}
        path  = [element_classes[x[0]](float(x[1])) for x in raw_data]

        # Set drift lengths
        for i in range(len(path)):
            if path[i].get_type() == 'drift':
                path[i].set_length(path[i+1].s-path[i].s)

        return path

    def get_elements(self, which):
        return [x for x in self.path if x.get_type() == which]


# Collect data on electron and photon beams at time t.
class MagnetStrengths(object):


    def __init__(self):
        self.path = Layout().path
        self.kick_add = np.array([0,0,0,0,0])

    # Define alterations to the kickers.
    def step_k3(self, factor):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.STEP_K3)

    def bump_left(self, factor):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.BUMP_LEFT)

    def bump_right(self, factor):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.BUMP_RIGHT)

    def bpm1(self, factor):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.BPM1)

    def bpm2(self, factor):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.BPM2)

    def scale(self, factor):

        self.kick_add = self.kick_add + factor*np.array([1,1,1,1,1]) # not working...

    def reset(self):

        self.kick_add = np.array([0,0,0,0,0])

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kicker_pos = [i.s for i in self.path if i.get_type() == 'kicker']
        d12 = float(kicker_pos[1] - kicker_pos[0])/float(kicker_pos[2] - kicker_pos[1])
        d34 = float(kicker_pos[3] - kicker_pos[2])/float(kicker_pos[4] - kicker_pos[3])
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 
        graphscale = 0.5
        kick = graphscale * max_kick * (np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               1, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.kick_add)

        return kick


class CollectData(object):


    def __init__(self):

        self.data = Layout()
        self.path = self.data.path
        self.magnets = MagnetStrengths()
        self.p_pos = [[self.data.get_elements('id')[0].s, 
                       self.data.get_elements('detector')[0].s],
                      [self.data.get_elements('id')[1].s, 
                       self.data.get_elements('detector')[0].s]]

    # Send electron vector through chicane magnets at time t.
    def timestep(self,t):

        # Initialise electron beam position and velocity
        e_beam = np.array([0,0])
        e_vector = [[0,0]]

        # Initialise photon beam position and velocity
        p_vector = []

        # Calculate positions of electron beam and photon beam relative to main axis.
        for kicker, strength in zip(self.data.get_elements('kicker'), 
                                self.magnets.calculate_strengths(t)):
            kicker.set_strength(strength)

        for p in self.path:
            if p.get_type() != 'detector':
                e_beam = p.increment(e_beam)
                e_vector.append(e_beam.tolist())
            if p.get_type() == 'id':
                p_vector.append(e_beam.tolist())

        # Create photon beams.
        travel = [Drift(self.data.get_elements('id')[0].s), 
                  Drift(self.data.get_elements('id')[1].s)]
        for i in range(2):
            travel[i].set_length(self.p_pos[i][1] - self.p_pos[i][0])
            p_vector[i].extend(travel[i].increment(p_vector[i]))

        return e_vector, p_vector # Returns pos and vel of electrons and photons.


####################
## Graph plotting ##
####################

class Plot(FigureCanvas):


    def __init__(self):

        self.info = CollectData()
        self.fig = plt.figure()
        FigureCanvas.__init__(self, self.fig)
        self.axes = self.fig_setup()
        self.beams = self.data_setup()

    def fig_setup(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_xlim(self.info.data.get_elements('drift')[0].s, self.info.data.get_elements('detector')[0].s)
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-3, 4)
        ax2 = self.fig.add_subplot(2, 1, 2)
        ax2.get_xaxis().set_visible(False)
        ax2.get_yaxis().set_visible(False)

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

        e_positions = np.array(self.info.timestep(t)[0])[:,0].tolist()
        # Remove duplicates in data.
        for i in range(len(self.info.data.get_elements('drift'))):
            if e_positions[i] == e_positions[i+1]:
                e_positions.pop(i+1)

        p_positions = np.array(self.info.timestep(t)[1])[:,[0,2]]

        return e_positions, p_positions

    # Animation function
    def animate(self, t):
#        t = t*4 # This gets it to one cycle per second.

        # Obtain data for plotting.
        data = self.beam_plot(t)
        e_data = data[0]
        p_data = data[1]

        xaxis = [0]
        xaxis.extend([i.s for i in self.info.data.path if i.get_type() != 'drift'])

        beams = self.init_data()
        beams[0].set_data(xaxis, e_data)
        for line, x, y in zip([beams[1],beams[2]], 
                          self.info.p_pos, p_data):
            line.set_data(x,y)

        return beams

    def show_plot(self):

        # Plot positions of kickers and IDs.
        for i in self.info.data.get_elements('kicker'):
            self.axes[0].axvline(x=i.s, color='k', linestyle='dashed')
        for i in self.info.data.get_elements('id'):
            self.axes[0].axvline(x=i.s, color='r', linestyle='dashed')

        xclr = (self.info.data.get_elements('kicker')[2].s,
                self.info.data.get_elements('detector')[0].s)
        yclr = (0,self.beam_plot(150)[1][1][1])
        yclr2 = (0,self.beam_plot(50)[1][0][1]) # feels wrong to hard code these numbers
        self.axes[0].fill_between( xclr, yclr, yclr2, facecolor='yellow', alpha=0.2) # facecolor=[(1,1,0,0.2)])

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
        self.ui.scaleplusButton.clicked.connect(lambda: self.scale(2))
        self.ui.scaleminusButton.clicked.connect(lambda: self.scale(-2))
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.graph.show_plot()
        self.ui.graph.gauss_plot()

    def k3(self, n):
        self.ui.graph.info.magnets.step_k3(n)

    def bump_left(self, n):
        self.ui.graph.info.magnets.bump_left(n)

    def bump_right(self, n):
        self.ui.graph.info.magnets.bump_right(n)

    def bpm1(self, n):
        self.ui.graph.info.magnets.bpm1(n)

    def bpm2(self, n):
        self.ui.graph.info.magnets.bpm2(n)

    def scale(self, n):
        self.ui.graph.info.magnets.scale(n)

    def reset(self):
        self.ui.graph.info.magnets.reset()

def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


