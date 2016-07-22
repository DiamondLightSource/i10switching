#!/usr/bin/env dls-python2.7
#i10plots
# Contains BaseFigureCanvas, Simulation, OverlaidWaveforms, Traces, RangeError
# Calls i10straight

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from cothread.catools import caget, camonitor
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)
import scipy.integrate as integ

import i10straight


class BaseFigureCanvas(FigureCanvas):

    """Initialise the figures for plotting."""

    def __init__(self):
        self.figure = plt.figure()
        self.figure.patch.set_facecolor('blue')
        self.figure.patch.set_alpha(0.0)
        FigureCanvas.__init__(self, self.figure)


class Simulation(BaseFigureCanvas):

    """Plot the simulation of the I10 fast chicane."""

    def __init__(self, collectdata):

        self.info = collectdata
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
            ax1.axvline(x=i.s, color='b', linestyle='dashed')

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

        beam1max = edges[0][0]
        beam1min = edges[1][0]
        beam2max = edges[1][1]
        beam2min = edges[0][1]

        self.fill1 = self.ax.fill_between(self.info.data.p_coord[0],
                               beam1min, beam1max, facecolor='blue', alpha=0.2)
        self.fill2 = self.ax.fill_between(self.info.data.p_coord[1],
                               beam2min, beam2max, facecolor='green', alpha=0.2)

    def magnet_limits(self):

        strengths = [np.array([caget('SR09A-PC-FCHIC-01:IMAX'),
                              -caget('SR09A-PC-FCHIC-02:IMAX'),
                               caget('SR10S-PC-FCHIC-03:IMAX'), 0, 0]),
                     np.array([0, 0, caget('SR10S-PC-FCHIC-03:IMAX'),
                              -caget('SR10S-PC-FCHIC-04:IMAX'), 
                               caget('SR10S-PC-FCHIC-05:IMAX')])]

#        strengths = np.array([caget('SR09A-PC-FCHIC-01:IMAX'),
#                              caget('SR09A-PC-FCHIC-02:IMAX'),
#                              caget('SR10S-PC-FCHIC-03:IMAX'),
#                              caget('SR10S-PC-FCHIC-04:IMAX'), 
#                              caget('SR10S-PC-FCHIC-05:IMAX')])

        # problem with plotting - currently incorrect but how to make it right??
        # takes 30 clicks of bump left + to go out of magnet range...
        edges = [[], []]
        for s in range(2):
            edges[s] = np.array(self.info.p_beam_lim(strengths[s]))[:, [0, 2]]

        beam1max = edges[0][0]
        beam2max = edges[1][1]

        self.limit1 = self.ax.plot(self.info.data.p_coord[0], beam1max, 'r--')
        self.limit2 = self.ax.plot(self.info.data.p_coord[1], beam2max, 'r--')

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

    def get_windowed_data(self, value): # I think this works...

        try:
            diff = np.diff(self.trigger).tolist()
            length = len(value)
            stepvalue = 0.001 # hard coded as assumed step will be larger than this and noise smaller - ok to do??

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
        self.gauss = self.ax.plot(a*np.exp(-(np.linspace(0, len(self.x),
                        len(self.x))-len(self.x)/2)**2/(2*sigma**2)), 'r')
        self.lines.append(self.gauss)
        self.draw()

    def clear_gaussian(self):
        self.ax.lines.pop(-1)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()

class Traces(BaseFigureCanvas): # can't get cothread to work - threading issue??

    def __init__(self):
        BaseFigureCanvas.__init__(self)
        self.ax = self.figure.add_subplot(1, 1, 1)
#        pv1 = i10straight.i10controls.TRACES[0] #'BL10I-EA-USER-01:WAI1'
#        pv2 = i10straight.i10controls.TRACES[1]

        # Initialise with real data the first time to set axis ranges
#        i10controls.register_listener(self.update_traces)
#        trigger = i10controls.arrays[i10controls.ARRAYS.TRIGGER]
#        trace = i10controls.arrays[i10controls.ARRAYS.TRACE]
#        x = range(len(trace))
#        self.lines = [
#                     self.ax.plot(x, trigger, 'b')[0],
#                     self.ax.plot(x, trace, 'g')[0]
#                     ]


#        camonitor(pv1, self.update_trigger)
#        camonitor(pv2, self.update_trace)

#    def update_traces(self, key, index):

#        if key == i10controls.ARRAYS.TRIGGER:
#            self.lines[0].set_ydata(i10controls.arrays[key])
#            self.draw()
#        elif key == i10controls.ARRAYS.TRACES:
#            self.lines[1].set_ydata(i10controls.arrays[key])
#            self.draw()

#    def update_trigger(self, value):

#        self.lines[0].set_ydata(value)
#        self.draw()

#    def update_trace(self, value):

#        self.lines[1].set_ydata(value)
#        self.draw()

class RangeError(Exception):

    """Raised when the trace data is partially cut off."""

    pass


