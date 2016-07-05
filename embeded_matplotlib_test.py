#!/bin/env dls-python

import dls_packages

import cothread
from cothread.catools import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic

from pylab import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

import random
import os


UI_FILENAME = 'matplotlib_test.ui'
PV = 'SR-DI-EBPM-01:SA:X'


class MyTestCanvas(FigureCanvas):
    def __init__(self):
        self.scale_val = 1
        self.figure = plt.figure()
        FigureCanvas.__init__(self, self.figure)
        self.axes = self.figure.add_subplot(1, 1, 1)

        # Initialise with real data the first time to set axis ranges
        data = caget(PV)
        x, y = (range(len(data)), data)
        self.lines = self.axes.plot(x, y)[0]
        camonitor(PV, self.update_plot)

    def update_plot(self, value):
        self.lines.set_ydata(value)
        self.draw()


class TestUi(QMainWindow):

    def __init__ (self ):
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)

        self.ui.graph = MyTestCanvas()
        self.ui.matplotlib_layout.addWidget(self.ui.graph)


def main():
    cothread.iqt()
    test_ui = TestUi()
    test_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()

