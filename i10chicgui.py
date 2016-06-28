# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'i10chicgui.ui'
#
# Created: Tue Jun 28 13:16:23 2016
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_i10gui(object):
    def setupUi(self, i10gui):
        i10gui.setObjectName(_fromUtf8("i10gui"))
        i10gui.resize(808, 479)
        i10gui.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(i10gui)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.kplusButton = QtGui.QPushButton(self.centralwidget)
        self.kplusButton.setObjectName(_fromUtf8("kplusButton"))
        self.gridLayout.addWidget(self.kplusButton, 1, 0, 1, 1)
        self.pushButton = QtGui.QPushButton(self.centralwidget)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.gridLayout.addWidget(self.pushButton, 1, 1, 1, 1)
        self.pushButton_3 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.gridLayout.addWidget(self.pushButton_3, 1, 2, 1, 1)
        self.pushButton_5 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_5.setObjectName(_fromUtf8("pushButton_5"))
        self.gridLayout.addWidget(self.pushButton_5, 1, 3, 1, 1)
        self.pushButton_7 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_7.setObjectName(_fromUtf8("pushButton_7"))
        self.gridLayout.addWidget(self.pushButton_7, 1, 4, 1, 1)
        self.plotButton = QtGui.QPushButton(self.centralwidget)
        self.plotButton.setObjectName(_fromUtf8("plotButton"))
        self.gridLayout.addWidget(self.plotButton, 1, 5, 1, 1)
        self.kminusButton = QtGui.QPushButton(self.centralwidget)
        self.kminusButton.setObjectName(_fromUtf8("kminusButton"))
        self.gridLayout.addWidget(self.kminusButton, 2, 0, 1, 1)
        self.pushButton_2 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton_4 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.gridLayout.addWidget(self.pushButton_4, 2, 2, 1, 1)
        self.pushButton_6 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_6.setObjectName(_fromUtf8("pushButton_6"))
        self.gridLayout.addWidget(self.pushButton_6, 2, 3, 1, 1)
        self.pushButton_8 = QtGui.QPushButton(self.centralwidget)
        self.pushButton_8.setObjectName(_fromUtf8("pushButton_8"))
        self.gridLayout.addWidget(self.pushButton_8, 2, 4, 1, 1)
        self.quitButton = QtGui.QPushButton(self.centralwidget)
        self.quitButton.setObjectName(_fromUtf8("quitButton"))
        self.gridLayout.addWidget(self.quitButton, 2, 5, 1, 1)
        self.matplotlib_layout = QtGui.QVBoxLayout()
        self.matplotlib_layout.setObjectName(_fromUtf8("matplotlib_layout"))
        self.gridLayout.addLayout(self.matplotlib_layout, 0, 0, 1, 4)
        i10gui.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(i10gui)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 808, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        i10gui.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(i10gui)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        i10gui.setStatusBar(self.statusbar)
        self.actionStuff = QtGui.QAction(i10gui)
        self.actionStuff.setObjectName(_fromUtf8("actionStuff"))

        self.retranslateUi(i10gui)
        QtCore.QMetaObject.connectSlotsByName(i10gui)

    def retranslateUi(self, i10gui):
        i10gui.setWindowTitle(QtGui.QApplication.translate("i10gui", "i10chic_gui", None, QtGui.QApplication.UnicodeUTF8))
        self.kplusButton.setText(QtGui.QApplication.translate("i10gui", "K3 +", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("i10gui", "H BPM1 +", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_3.setText(QtGui.QApplication.translate("i10gui", "H BPM2 +", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_5.setText(QtGui.QApplication.translate("i10gui", "BUMP LEFT +", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_7.setText(QtGui.QApplication.translate("i10gui", "BUMP RIGHT +", None, QtGui.QApplication.UnicodeUTF8))
        self.plotButton.setText(QtGui.QApplication.translate("i10gui", "Plot", None, QtGui.QApplication.UnicodeUTF8))
        self.kminusButton.setText(QtGui.QApplication.translate("i10gui", "K3 -", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_2.setText(QtGui.QApplication.translate("i10gui", "H BPM1 -", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_4.setText(QtGui.QApplication.translate("i10gui", "H BPM2 -", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_6.setText(QtGui.QApplication.translate("i10gui", "BUMP LEFT -", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_8.setText(QtGui.QApplication.translate("i10gui", "BUMP RIGHT -", None, QtGui.QApplication.UnicodeUTF8))
        self.quitButton.setText(QtGui.QApplication.translate("i10gui", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionStuff.setText(QtGui.QApplication.translate("i10gui", "Stuff", None, QtGui.QApplication.UnicodeUTF8))

