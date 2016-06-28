#!/bin/env dls-python

import dls_packages

import cothread
from cothread.catools import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pylab import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import random

from matplotlib_test import Ui_MainWindow


class MyTestCanvas(FigureCanvas):
    pass


class TestUi(object):

    def __init__ (self, parent):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(parent)

        self.figure = plt.figure()
        self.ui.graph = FigureCanvas(self.figure)
        self.ui.matplotlib_layout.addWidget(self.ui.graph)

        self.ui.plot_button.clicked.connect(self.plot)
        self.plot()

    def plot(self):
        data = [random.random() for i in range(10)]
        ax = self.figure.add_subplot(111)
        ax.hold(False)
        ax.plot(data, '*-')
        self.ui.graph.draw()


def main():
    cothread.iqt()
    window = QMainWindow()
    test_ui = TestUi(window)  # Must hold onto the instance
    window.show()
    cothread.WaitForQuit()


if __name__ == '__main__':
    main()

