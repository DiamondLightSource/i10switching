#i10plots
# Contains BaseFigureCanvas, Simulation, GaussPlot, OverlaidWaveforms, Traces, 
# RangeError
# TODO replace GaussPlot by a graph that actually plots a gaussian?? no, set 
# functionality so you can overlay a gaussian on peaks?
# Calls i10straight
# Need to rename classes to be more sensible

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from cothread.catools import caget, camonitor
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)
import scipy.integrate as integ

import i10straight


########################
#### Graph plotting ####
########################

class BaseFigureCanvas(FigureCanvas):

    def __init__(self):
        self.figure = plt.figure()
        FigureCanvas.__init__(self, self.figure)


class Simulation(BaseFigureCanvas):

    def __init__(self):

        self.info = i10straight.CollectData()
        BaseFigureCanvas.__init__(self)
        self.ax = self.fig_setup()
        self.beams = self.data_setup()

        self.anim = animation.FuncAnimation(self.figure, self.animate,
                    init_func=self.init_data, frames=1000, interval=20)

    def fig_setup(self):

        # Set up axes
        ax1 = self.figure.add_subplot(1, 1, 1)
        ax1.set_xlim(self.info.data.path[0].s, self.info.data.path[-1].s)
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-0.01, 0.01)
        # Plot positions of kickers and IDs.
        for i in self.info.data.kickers:
            ax1.axvline(x=i.s, color='k', linestyle='dashed')
        for i in self.info.data.ids:
            ax1.axvline(x=i.s, color='r', linestyle='dashed')

        return ax1

    def data_setup(self):

        beams = [
                self.ax.plot([], [], 'b')[0],
                self.ax.plot([], [], 'r')[0],
                self.ax.plot([], [], 'r')[0]
                ]

        return beams

    def init_data(self):

        for line in self.beams:
            line.set_data([], [])

        return self.beams

    # Extract electron and photon beam positions for plotting.
    def beam_plot(self, t):

        e_positions = np.array(self.info.timestep(t)[0])[:, 0].tolist()
        # Remove duplicates in data.
        for i in range(len(self.info.data.get_elements('drift'))):
            if e_positions[i] == e_positions[i+1]:
                e_positions.pop(i+1)

        p_positions = np.array(self.info.timestep(t)[1])[:, [0, 2]]

        return e_positions, p_positions

    # Animation function
    def animate(self, t):
#        t = t*4 # This gets it to one cycle per second.

        # Obtain data for plotting.
        data = self.beam_plot(t)
        e_data = data[0]
        p_data = data[1]

        beams = self.init_data()
        beams[0].set_data(self.info.data.xaxis, e_data)
        for line, x, y in zip([beams[1], beams[2]],
                          self.info.data.p_coord, p_data):
            line.set_data(x, y)

        return beams

    def update_colourin(self):

        strengths = [np.array([1, -1, 1, 0, 0]), np.array([0, 0, 1, -1, 1])]
        edges = [[], []]
        for s in range(2):
            edges[s] = np.array(self.info.p_beam_range(strengths[s]))[:, [0, 2]]

        beam1min = edges[0][0]
        beam1max = edges[1][0]
        beam2min = edges[1][1]
        beam2max = edges[0][1]

        self.fill1 = self.ax.fill_between(self.info.data.p_coord[0],
                               beam1min, beam1max, facecolor='blue', alpha=0.2)
        self.fill2 = self.ax.fill_between(self.info.data.p_coord[1],
                               beam2min, beam2max, facecolor='green', alpha=0.2)
# define here or in init?

class GaussPlot(BaseFigureCanvas):

    def __init__(self):
        BaseFigureCanvas.__init__(self)
        self.ax = self.figure.add_subplot(1, 1, 1)
        self.trigger = np.load('example_data/trigger.npy')
        self.trace = np.load('example_data/diode.npy')

    def display(self):

        try:
            diff = np.diff(self.trigger).tolist()
            length = len(self.trace)
            stepvalue = 0.1 # have I got exceptions in right places? should there be way to change it if it's wrong?

            if min(diff) > -1*stepvalue or max(diff) < stepvalue:
                raise RangeError

            maxtrig = next(x for x in diff if x > stepvalue)
            mintrig = next(x for x in diff if x < -1*stepvalue)
            edges = [diff.index(maxtrig), diff.index(mintrig)]

            trigger_length = (edges[1]-edges[0])*2

            if length < trigger_length:
                raise RangeError

            data = [[], []]
            label = [[], []]
            self.line = [[], []]
            for i in range(2):
                data[i] = np.roll(self.trace[:trigger_length], - edges[i]
                                  - trigger_length/4)[:trigger_length/2]
                label[i] = integ.simps(data[i])
                if label[i] < 0.1:
                    raise RangeError
                self.line[i] = self.ax.plot(data[i], label=integ.simps(data[i]))
            self.ax.legend()

        except RangeError:
            print 'Trace is partially cut off'
            self.line = [self.ax.plot(float('nan'),
                         label='Trace is partially cut off'),
                         self.ax.plot(float('nan'))]
            self.ax.legend()

    def gaussian(self, amplitude, sigma):
        self.ax.plot(amplitude*np.exp(-(np.linspace(0, len(self.trace), 2500)-len(self.trace)/2)**2/(2*sigma**2)))


class OverlaidWaveforms(BaseFigureCanvas):

    def __init__(self, pv1, pv2):
        BaseFigureCanvas.__init__(self)
        self.ax = self.figure.add_subplot(1, 1, 1)

        # Initialise with real data the first time to set axis ranges
        self.trigger = caget(pv1)

        data1, data2 = self.get_windowed_data(caget(pv2))
        self.x = range(len(data1))
        self.lines = [
                     self.ax.plot(self.x, data1, 'b')[0],
                     self.ax.plot(self.x, data2, 'g')[0]
                     ]

        camonitor(pv2, self.update_plot)


    def update_plot(self, value):

        data1, data2 = self.get_windowed_data(value)
        self.lines[0].set_ydata(data1)
        self.lines[1].set_ydata(data2)
#        self.scale+=1 # ??????????
        labels = [integ.simps(data1), integ.simps(data2)]
        for area in labels:
            if area < 0.1:
                raise RangeError
        self.ax.legend([self.lines[0], self.lines[1]],
                       labels)

        self.draw()

    def get_windowed_data(self, value): # I think this works but hard to tell without trying it on real data not noise

        try:
            diff = np.diff(self.trigger).tolist()
            length = len(value)
            stepvalue = 0.001 # hard coded as assumed step will be larger than this and noise smaller - ok to do?? # make it a config parameter

            if min(diff) > -1*stepvalue or max(diff) < stepvalue:
                raise RangeError

            maxtrig = next(x for x in diff if x > stepvalue)
            mintrig = next(x for x in diff if x < -1*stepvalue)
            edges = [diff.index(maxtrig), diff.index(mintrig)]

            trigger_length = (edges[1]-edges[0])*2

            if length < trigger_length:
                raise RangeError

            data1 = np.roll(value[:trigger_length], - edges[0]
                            - trigger_length/4)[:trigger_length/2]
            data2 = np.roll(value[:trigger_length], - edges[1]
                            - trigger_length/4)[:trigger_length/2]
            return data1, data2

        except RangeError:
            print 'Trace is partially cut off' # status bar? callback?
            data1 = [float('nan'), float('nan')]
            data2 = [float('nan'), float('nan')]
            return data1, data2

    def gaussian(self, a, sigma):
        self.gauss = self.ax.plot(a*np.exp(-(np.linspace(0, len(self.x), len(self.x))-len(self.x)/2)**2/(2*sigma**2)), 'r')
        self.lines.append(self.gauss)
        self.draw()

    def clear_gaussian(self):
        self.ax.lines.pop(-1)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class Traces(BaseFigureCanvas):

    def __init__(self, pv1, pv2):
        BaseFigureCanvas.__init__(self)
        self.ax = self.figure.add_subplot(1, 1, 1)

        # Initialise with real data the first time to set axis ranges
        trigger = caget(pv1)
        trace = caget(pv2)
        x = range(len(trace))
        self.lines = [
                     self.ax.plot(x, trigger, 'b')[0],
                     self.ax.plot(x, trace, 'g')[0]
                     ]
        camonitor(pv1, self.update_trigger)
        camonitor(pv2, self.update_trace)

    def update_trigger(self, value):

        self.lines[0].set_ydata(value)
        self.draw()

    def update_trace(self, value):

        self.lines[1].set_ydata(value)
        self.draw()

class RangeError(Exception):

    """Raised when the trace data is partially cut off."""

    pass


