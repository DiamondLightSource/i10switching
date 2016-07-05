
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
        resetButton.clicked.connect(self.reset)
        resetButton.clicked.connect(self.plotting)

        kplusButton = QtGui.QPushButton("K +",self)
        kplusButton.clicked.connect(self.kplus)
        kplusButton.clicked.connect(self.plotting)
        kplusButton.move(100, 0)

        kminusButton = QtGui.QPushButton("K -",self)
        kminusButton.clicked.connect(self.kminus)
        kminusButton.clicked.connect(self.plotting)
        kminusButton.move(100,30)

        quitButton = QtGui.QPushButton("Quit",self)
        quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        quitButton.move(0, 30)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('i10chic GUI')    
        self.resize(250, 150)
        self.show()

    def kplus(self):
        
        self.k += 1
        return self.k

    def kminus(self):
        
        self.k -= 1
        return self.k

    def reset(self):
        
        self.k = 10
        plt.close()
        plt.plot(self.k,self.k,'.')
        plt.show()
        return self.k

    def plotting(self):

        plt.plot(self.k,self.k,'.')
        plt.draw()
        plt.show()

        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Control()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


