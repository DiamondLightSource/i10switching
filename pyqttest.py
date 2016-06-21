
######################################
######################################
############# GUI TEST ###############
######################################
######################################


# Initial attempt at GUI for i10chic.py

import dls_packages
import sys
from PyQt4 import QtGui, QtCore
import matplotlib.pyplot as plt
import numpy as np

class Control(QtGui.QMainWindow):
    k = 10

    def __init__(self):
        super(Control, self).__init__()
        self.initUI()
        self.k
    
    def initUI(self):
        
        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        
        resetButton = QtGui.QPushButton("Reset",self)

        graphButton = QtGui.QPushButton("Plot graph",self)
        graphButton.clicked.connect(self.plotting)
        graphButton.move(100, 30)

        kButton = QtGui.QPushButton("K +",self)
        kButton.clicked.connect(self.kplus)
        kButton.move(100, 0)

        quitButton = QtGui.QPushButton("Quit",self)
        quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        quitButton.move(0, 30)

        '''
        # Layout stuff
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addStretch(1)
        hbox1.addWidget(resetButton)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(kButton)
        hbox.addWidget(quitButton)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        '''
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('i10chic GUI')    
        self.resize(250, 150)
        self.center()

        self.show()

    def kplus(self):
        
        self.k += 1
        self.plotting()
        print self.k

    def center(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def plotting(self):

        plt.plot(np.arange(self.k),np.arange(self.k)) # so just need plot command here, have a separate set data function which is updated by kplus. Should work...
        plt.show()
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Control()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


