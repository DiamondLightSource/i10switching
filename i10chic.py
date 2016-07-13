# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

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
from PyQt4 import uic
from PyQt4.QtGui import QMainWindow
import os
import scipy.integrate as integ
from scipy.constants import c

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
    SCALE = [0.01,0.01,0,0.01,0.01]

    SHIFT = [STEP_K3, BUMP_LEFT, BUMP_RIGHT, BPM1, BPM2, SCALE]


# Assign locations of devices along the axis of the system.

class Layout(object):

    NAME = 'config.txt'

    def __init__(self):
        self.path = self.load()

    def load(self):

        raw_data = [line.split() for line in open(self.NAME)]
        element_classes = {cls(None).get_type(): cls 
                           for cls in Element.__subclasses__()}
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
    BEAM_RIGIDITY = 3e9/c
    # Conversion values between current and tesla for the kickers.
    AMP_TO_TESLA = np.array([0.034796/23, 0.044809/23, 0.011786/12, 
                             0.045012/23, 0.035174/23])
    CURRENTS = np.array([23.261, 23.2145, 10.188844, 23.106842, 23.037771])
    FIELDS = CURRENTS*AMP_TO_TESLA

    def __init__(self):
        self.path = Layout().path
        self.kick_add = np.array([0,0,0,0,0])

        self.max_kick = np.array([2 * np.arcsin(x/(2*self.BEAM_RIGIDITY)) 
                                  for x in self.FIELDS])

    # Define alterations to the kickers.
    def buttons(self, factor, button):

        self.kick_add = self.kick_add + factor*np.array(ButtonData.SHIFT[button])

    def reset(self):

        self.kick_add = np.array([0,0,0,0,0])

    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):

        kick = self.max_kick * (np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               2, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1]) + self.kick_add)

        return kick 


class CollectData(object):


    def __init__(self):

        self.data = Layout()
        self.path = self.data.path
        self.magnets = MagnetStrengths()
        self.ids = self.data.get_elements('id')
        self.kickers = self.data.get_elements('kicker')
        self.detector = self.data.get_elements('detector')
        self.drifts = self.data.get_elements('drift')
        self.p_coord = [[self.ids[0].s, 
                         self.detector[0].s],
                        [self.ids[1].s, 
                         self.detector[0].s]]
        self.travel = [Drift(self.ids[0].s), 
                       Drift(self.ids[1].s)]

    def strength_setup(self, strength_values):

        for kicker, strength in zip(self.kickers, strength_values):
            kicker.set_strength(strength)

    def create_photon_beam(self, vector):

        for i in range(2):
            self.travel[i].set_length(self.p_coord[i][1] - self.p_coord[i][0])
            vector[i].extend(self.travel[i].increment(vector[i]))

        return vector

    def send_electrons_through(self):

        e_vector = np.array([0,0])
        e_beam = np.zeros((len(self.path),2))
        p_vector = []

        # Send e_vector through system and create electron and photon beams
        for p in self.path:
            if p.get_type() != 'detector':
                e_vector = p.increment(e_vector)
                e_beam[self.path.index(p)+1] = e_vector
            if p.get_type() == 'id':
                p_vector.append(e_vector.tolist()) # here need it to be a list and indexes don't match up nicely anyway
        p_beam = self.create_photon_beam(p_vector)

        return e_beam, p_beam

    # Create e and p beams at time t
    def timestep(self,t):

        self.strength_setup(self.magnets.calculate_strengths(t))

        beams = self.send_electrons_through()
        e_beam = beams[0]
        p_beam = beams[1]

        return e_beam, p_beam # Returns pos and vel of electrons and photons.

    # Calculate p beams for fixed magnet strengths
    def p_beam_range(self, strength_values):

        self.strength_setup(self.magnets.max_kick 
                            * (strength_values + self.magnets.kick_add))

        p_beam = self.send_electrons_through()[1]


        return p_beam

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

        ax1 = self.fig.add_subplot(1, 1, 1)
        ax1.set_xlim(self.info.drifts[0].s, self.info.detector[0].s)
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-0.02, 0.02)

        return ax1

    def data_setup(self):

        beams = [
                self.axes.plot([], [])[0], 
                self.axes.plot([], [], 'r')[0], 
                self.axes.plot([], [], 'r')[0]
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
        for i in range(len(self.info.drifts)):
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
                          self.info.p_coord, p_data):
            line.set_data(x,y)

        return beams

    def show_plot(self):

        # Plot positions of kickers and IDs.
        for i in self.info.kickers:
            self.axes.axvline(x=i.s, color='k', linestyle='dashed')
        for i in self.info.ids:
            self.axes.axvline(x=i.s, color='r', linestyle='dashed')

        # Create animations
        self.anim = animation.FuncAnimation(self.fig, self.animate, 
                    init_func=self.init_data, frames=1000, interval=20)

    def update_colourin(self):

        strengths1 = np.array([2,-2,2,0,0])
        strengths2 = np.array([0,0,2,-2,2])

        edges1 = np.array( self.info.p_beam_range(strengths1) )[:,[0,2]]
        edges2 = np.array( self.info.p_beam_range(strengths2) )[:,[0,2]]

        beam1min = edges1[0]
        beam1max = edges2[0]
        beam2min = edges2[1]
        beam2max = edges1[1]

        self.fill1 = self.axes.fill_between(self.info.p_coord[0], 
                               beam1min, beam1max, facecolor='blue', alpha=0.2)
        self.fill2 = self.axes.fill_between(self.info.p_coord[1], 
                               beam2min, beam2max, facecolor='green', alpha=0.2)


class GaussPlot(FigureCanvas):

    def __init__(self):
        self.figure = plt.figure()
        FigureCanvas.__init__(self, self.figure)
        self.ax1 = self.figure.add_subplot(1, 1, 1)
        self.trigger = np.load('trigger.npy')
        self.trace = np.load('diode.npy')

    def display(self):

        try:
            diff = np.diff(self.trigger).tolist()
            length = len(self.trace)
            stepvalue = 0.1 # hard coded as assumed step will be larger than this and noise smaller - ok to do??

            if min(diff) > -1*stepvalue or max(diff) < stepvalue:
                raise RangeError

            maxtrig = next(x for x in diff if x > stepvalue)
            mintrig = next(x for x in diff if x < -1*stepvalue)
            edges = [diff.index(maxtrig),diff.index(mintrig)]

            trigger_length = (edges[1]-edges[0])*2

            if length < trigger_length:
                raise RangeError

            data1 = np.roll(self.trace[:trigger_length], - edges[0] - trigger_length/4)[:trigger_length/2]
            data2 = np.roll(self.trace[:trigger_length], - edges[1] - trigger_length/4)[:trigger_length/2]
            self.ax1.plot(data1, label = integ.simps(data1))
            self.ax1.plot(data2, label = integ.simps(data2))
            self.ax1.legend()

        except RangeError:
            print 'Trace is partially cut off'
            self.ax1.plot(range(10), 'r', label = 'Trace is partially cut off')
            self.ax1.plot(range(9,-1,-1), 'r')
            self.ax1.legend()

#put in trace graph here

class WaveformCanvas(FigureCanvas):

    def __init__(self, pv1, pv2):
#        self.scale = 1
        self.figure = plt.figure()
        FigureCanvas.__init__(self, self.figure)
        self.ax1 = self.figure.add_subplot(1, 1, 1)

        # Initialise with real data the first time to set axis ranges
        self.trigger = caget(pv1)

        data1, data2 = self.get_windowed_data(caget(pv2))
        x = range(len(data1))
        self.lines = [
                     self.ax1.plot(x, data1, 'b')[0],
                     self.ax1.plot(x, data2, 'g')[0]
                     ]

        camonitor(pv2, self.update_plot)

    def update_plot(self, value):

        data1, data2 = self.get_windowed_data(value)
        self.lines[0].set_ydata(data1)
        self.lines[1].set_ydata(data2)
#        self.scale+=1 # ??????????
        self.ax1.legend([self.lines[0], self.lines[1]], 
                        [integ.simps(data1), integ.simps(data2)])

        self.draw()

    def get_windowed_data(self, value): # I think this works but hard to tell without trying it on real data not noise

        try:
            diff = np.diff(self.trigger).tolist()
            length = len(value)
            stepvalue = 0.1 # hard coded as assumed step will be larger than this and noise smaller - ok to do?? # make it a config parameter

            if min(diff) > -1*stepvalue or max(diff) < stepvalue:
                raise RangeError

            maxtrig = next(x for x in diff if x > stepvalue)
            mintrig = next(x for x in diff if x < -1*stepvalue)
            edges = [diff.index(maxtrig),diff.index(mintrig)]

            trigger_length = (edges[1]-edges[0])*2

            if length < trigger_length:
                raise RangeError

            data1 = np.roll(value[:trigger_length], - edges[0] - trigger_length/4)[:trigger_length/2]
            data2 = np.roll(value[:trigger_length], - edges[1] - trigger_length/4)[:trigger_length/2]
            return data1, data2

        except RangeError:
            print 'Trace is partially cut off' # status bar? callback?
            data1 = [float('nan'), float('nan')]
            data2 = [float('nan'), float('nan')]
            return data1, data2


class RangeError(Exception):
    '''Raised when the trace data is partially cut off'''
    pass


###########################
########### GUI ###########
###########################

UI_FILENAME = 'i10chicgui.ui'


class Gui(QMainWindow):

    I10_ADC_1_PV = 'BL10I-EA-USER-01:WAI1'
    I10_ADC_2_PV = 'BL10I-EA-USER-01:WAI2'
    I10_ADC_3_PV = 'BL10I-EA-USER-01:WAI3'

    def __init__ (self):
        QMainWindow.__init__(self)
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)

        self.ui.graph = Plot()
        self.ui.graph2 = WaveformCanvas(self.I10_ADC_1_PV, self.I10_ADC_2_PV)
        self.ui.graph3 = GaussPlot()
        self.toolbar = NavigationToolbar(self.ui.graph3, self)

        self.ui.matplotlib_layout.addWidget(self.ui.graph)
        self.ui.matplotlib_layout.addWidget(self.ui.graph2)
        self.ui.matplotlib_layout.addWidget(self.ui.graph3)
        self.ui.matplotlib_layout.addWidget(self.toolbar)

        self.ui.kplusButton.clicked.connect(lambda: self.btn_ctrls(1,0))
        self.ui.kminusButton.clicked.connect(lambda: self.btn_ctrls(-1,0))
        self.ui.bumpleftplusButton.clicked.connect(lambda: self.btn_ctrls(1,1))
        self.ui.bumpleftminusButton.clicked.connect(lambda: self.btn_ctrls(-1,1))
        self.ui.bumprightplusButton.clicked.connect(lambda: self.btn_ctrls(1,2))
        self.ui.bumprightminusButton.clicked.connect(lambda: self.btn_ctrls(-1,2))
        self.ui.bpm1plusButton.clicked.connect(lambda: self.btn_ctrls(1,3))
        self.ui.bpm1minusButton.clicked.connect(lambda: self.btn_ctrls(-1,3))
        self.ui.bpm2plusButton.clicked.connect(lambda: self.btn_ctrls(1,4))
        self.ui.bpm2minusButton.clicked.connect(lambda: self.btn_ctrls(-1,4))
        self.ui.scaleplusButton.clicked.connect(lambda: self.btn_ctrls(1,5))
        self.ui.scaleminusButton.clicked.connect(lambda: self.btn_ctrls(-1,5))
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.quitButton.clicked.connect(sys.exit)

        self.ui.graph.show_plot()
        self.ui.graph.update_colourin()
        self.ui.graph3.display()

    def btn_ctrls(self, factor, which_button):
        self.ui.graph.info.magnets.buttons(factor, which_button)
        self.ui.graph.axes.collections.remove(self.ui.graph.fill1)
        self.ui.graph.axes.collections.remove(self.ui.graph.fill2)
        self.ui.graph.update_colourin()

    def reset(self):
        self.ui.graph.info.magnets.reset()
        self.ui.graph.axes.collections.remove(self.ui.graph.fill1)
        self.ui.graph.axes.collections.remove(self.ui.graph.fill2)
        self.ui.graph.update_colourin()

def main():
    cothread.iqt()
    the_ui = Gui()
    the_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()


