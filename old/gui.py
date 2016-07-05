
# Initial attempt at adding GUI to control the simulation.
import dls_packages
import sys
from PyQt4 import QtGui, QtCore

class Control(QtGui.QMainWindow):

    def __init__(self):
        super(Control, self).__init__()
        self.initUI()
        self.k3strength = 1

    def initUI(self):

        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        btn = QtGui.QPushButton("Plot",self)
        btn.clicked.connect(self.plotgraphs)
        # then add extra buttons to adjust things

        k3Button = QtGui.QPushButton("K3 +",self) # NOT CURRENTLY WORKING
        k3Button.clicked.connect(self.k3plus)
        k3Button.move(100, 30)

        quitButton = QtGui.QPushButton("Quit",self)
        quitButton.clicked.connect(QtCore.QCoreApplication.instance().quit)
        quitButton.move(0, 30)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('i10chic GUI')    
        self.resize(250, 150)
        self.centre()
        self.show()

    def plotgraphs(self):
        return Create_plots().show_plot()

    def k3(self):
        return self.k3strength

    def k3plus(self):
        self.k3strength += 1
        return self.k3strength

    def centre(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Control()
    sys.exit(app.exec_())





