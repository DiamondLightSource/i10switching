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

from matplotlib_test import Ui_MainWindow


UI_FILENAME = 'matplotlib_test.ui'


class MyTestCanvas(FigureCanvas):
    def __init__(self):
        self.scale_val = 1
        self.figure = plt.figure()
        FigureCanvas.__init__(self, self.figure)
        self.plot = self.figure.add_subplot(1, 1, 1)
        self.plot.set_xlim(0, 10)
        self.plot.set_ylim(0, 10)
        self.axis = self.plot.plot([])[0]
        self.ani = animation.FuncAnimation(
                self.figure, self.animate, frames=1000, interval=1000/60)

    def animate(self, _):
        data = [random.random() for i in range(10)]
        data = [x * self.scale_val for x in data]
        xy = [range(len(data)), data]
        self.axis.set_data(xy)

    def scale(self, factor):
        self.scale_val = self.scale_val * factor


class TestUi(QMainWindow):

    def __init__ (self ):
        filename = os.path.join(os.path.dirname(__file__), UI_FILENAME)
        self.ui = uic.loadUi(filename)

        self.ui.graph = MyTestCanvas()
        self.ui.matplotlib_layout.addWidget(self.ui.graph)
        self.ui.plot_button.clicked.connect(self.adjust)

    def adjust(self):
        self.ui.graph.scale(2)


def main():
    cothread.iqt()
    test_ui = TestUi()
    test_ui.ui.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()

