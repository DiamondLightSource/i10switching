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
from accelerators_ui import Gui


class GuiTests(unittest.TestCase):

    def test_import(self):
        pass

