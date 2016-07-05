import dls_packages
import sys
from PyQt4 import QtGui, QtCore, uic

form_class = uic.loadUiType("guitest.ui")[0]

class MyWindowClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
app = QtGui.QApplication(sys.argv)
myWindow = MyWindowClass()
myWindow.show()
app.exec_()

