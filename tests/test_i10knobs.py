from pkg_resources import require
require("cothread==2.10")
require("mock")
import unittest
import cothread
import sys
import os
from PyQt4 import QtGui

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import i10knobs

class I10KnobsTest(unittest.TestCase):


    def test_init(self):
        cothread.iqt()
        window = QtGui.QMainWindow()
        _ = i10knobs.KnobsUi(window)

