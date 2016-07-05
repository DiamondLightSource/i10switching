# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'matplotlib_test.ui'
#
# Created: Tue Jun 28 12:59:02 2016
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(321, 240)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.matplotlib_layout = QtGui.QVBoxLayout()
        self.matplotlib_layout.setObjectName(_fromUtf8("matplotlib_layout"))
        self.verticalLayout.addLayout(self.matplotlib_layout)
        self.plot_button = QtGui.QPushButton(self.centralwidget)
        self.plot_button.setObjectName(_fromUtf8("plot_button"))
        self.verticalLayout.addWidget(self.plot_button)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.plot_button.setText(QtGui.QApplication.translate("MainWindow", "Plot!", None, QtGui.QApplication.UnicodeUTF8))

