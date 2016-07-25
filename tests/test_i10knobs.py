from pkg_resources import require
require("cothread")
require("mock")
import unittest
import mock
import sys

# Mock out catools as it requires EPICS binaries at import
sys.modules['cothread.catools'] = mock.MagicMock()
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

