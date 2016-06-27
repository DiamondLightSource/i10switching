# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
from PyQt4 import QtGui, QtCore


# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.

class Drift(object):


    def __init__(self, step=0, where=0):
        self.step = step
        self.where = where

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'drift'


class Kicker(object):


    def __init__(self, k=0, where=0):
        self.k = k
        self.where = where

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'kicker'


class InsertionDevice(object):


    def __init__(self, where=0):
        self.where = where

    def increment(self, e):
        return e

    def set_position(self, where):
        self.where = where

    def coordinate(self):
        return self.where

    def get_type(self):
        return 'id'

# Assign the values of constants in the system:
# distances between devices and strength of 3rd kicker.

class Constants(object):

    LENGTHS = [2,2,4,4,4,4,2,20]


# Assign locations of devices along the axis of the system.

class Locate(object):


    def __init__(self):
        self.lengths = Constants().LENGTHS
        self.pathway = [
                  Drift(),Kicker(),
                  Drift(),Kicker(),
                  Drift(),InsertionDevice(),
                  Drift(),Kicker(),
                  Drift(),InsertionDevice(),
                  Drift(),Kicker(),
                  Drift(),Kicker(),
                  Drift()
                  ]

    def path(self): 
        return self.pathway

    def positions(self):
        
        pos = [0]
        pos.extend(np.cumsum(self.lengths))

        return pos

#    def locate_kicker(self):

#        pos = self.positions()
#        kicker_pos = [
#                     pos[1],
#                     pos[2],
#                     pos[4],
#                     pos[6],
#                     pos[7]
#                     ]
#        return kicker_pos

#    def locate_id(self):

#        pos = self.positions()
#        idpos = self.locate_devices()[1]

#        return idpos
#       self.locate_devices()
#        return [pos[3], pos[5]]
    
    def locate_detector(self):

        return self.positions()[8]

    def locate_photonbeam(self):

        return [[self.locate_devices()[1][0], self.locate_detector()],
                [self.locate_devices()[1][1], self.locate_detector()]]

    def get_elements(self, which):
        list_objects = []
        for p in self.pathway:
            if p.get_type() == which:
                list_objects.append(p)

        return list_objects

#########################################################################
    # Only partially working currently
    def locate_devices(self):

        kicker_pos = []
        id_pos = []
        devices = [x for x in self.path() if x.get_type() != 'drift']
        device_positions = self.positions()[1:]
        for device, where in zip(devices, device_positions):
            device.set_position(where)
        for device in devices:
            if device.get_type() == 'kicker':
                kicker_pos.append(device.coordinate())
            elif device.get_type() == 'id':
                id_pos.append(device.coordinate())

        return kicker_pos, id_pos


# Collect data on electron and photon beams at time t.

class Magnet_strengths(object):


    def __init__(self, k3=1):
        self.numbers = Constants()
        self.pos = Locate()
        self.k3 = k3

    def step_k3_plus(self, increment):
        self.k3 += increment

    def step_k3_minus(self, increment):
        self.k3 -= increment

    # Define magnet strength factors (dependent on relative positions and time).
    def max_magnet_strengths(self):

        kicker_pos = self.pos.locate_devices()[0]
        len1 = kicker_pos[1] - kicker_pos[0]
        len2 = kicker_pos[2] - kicker_pos[1]
        d12 = float(len1)/float(len2)
        len3 = kicker_pos[3] - kicker_pos[2]
        len4 = kicker_pos[4] - kicker_pos[3]
        d34 = float(len3)/float(len4)
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 
    
        return max_kick
    
    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self, t):
    
        graphscale = 0.5
        kicker3 = self.k3 # k3_strength.k3_value() #self.numbers.KICKER3
        kick = graphscale * self.max_magnet_strengths() * np.array([
               np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
               kicker3, np.sin(t*np.pi/100) - 1, -np.sin(t*np.pi/100)
               + 1])

        return kick


class Collect_data(object):


    def __init__(self):

        self.numbers = Constants()
        self.pos = Locate()
        self.path = self.pos.path()
#        self.e_vector = [[0,0]]
#        self.p_vector = []
    #PUT THIS IN A FUNCTION? OR CLASS?
    # Set drift distances (time independent).
        for drift, distance in zip(self.pos.get_elements('drift'), self.numbers.LENGTHS):
            drift.set_length(distance)
        self.magnets = Magnet_strengths()
    
    # Send electron vector through chicane magnets at time t.
    def timestep(self,t):
    
        # Initialise electron beam position and velocity
        e_beam = np.array([0,0])
        e_vector = [[0,0]]
    
        # Initialise photon beam position and velocity
        p_vector = []

        # Calculate positions of electron beam and photon beam relative to main axis.
        for kicker, strength in zip(self.pos.get_elements('kicker'), self.magnets.calculate_strengths(t)):
             kicker.set_strength(strength)

        for p in self.path:
            e_beam = p.increment(e_beam)
            device = p.get_type()
            e_vector.append(e_beam.tolist())
            if device == 'id':
                p_vector.append(e_beam.tolist())  # Electron vector passes through insertion device, photon vector created

        return e_vector, p_vector # Returns positions and velocities of electrons and photons.
    
    
    # Extract electron beam positions for plotting.
    def e_plot(self, e_beam):
    
        e_positions = np.array(e_beam)[:,0].tolist()
        # Remove duplicates in data.
        for i in range(len(self.pos.get_elements('drift'))):
            if e_positions[i] == e_positions[i+1]:
                e_positions.pop(i+1)
        
        return e_positions
    
    # Allow the two photon vectors to drift over large distance 
    # and add the vector for new position and velocity to 
    # original vector to create beam for plotting.
    def p_plot(self, p_beam):
        
        travel = [Drift(),Drift()]
        p_pos = self.pos.locate_photonbeam()
        for i in range(2):
            travel[i].set_length(p_pos[i][1]-p_pos[i][0])
            p_beam[i].extend(travel[i].increment(p_beam[i]))
    
        p_positions = np.array(p_beam)[:,[0,2]]
    
        return p_positions


####################
## Graph plotting ##
####################

class Plot(object):


    def __init__(self):

        self.lengths = Constants().LENGTHS
        self.positions = Locate()
        self.information = Collect_data()

        self.fig = plt.figure()
 
        self.other_data = [[],[],[],[]]
        self.axes = self.fig_setup()
        self.beams = self.data_setup()

    def fig_setup(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_xlim(0, sum(self.lengths))
        ax1.get_yaxis().set_visible(False)
        ax1.set_ylim(-2, 5)
        
        ax2 = self.fig.add_subplot(2, 2, 4)
        ax2.set_xlim(-10, 10)
        ax2.set_ylim(0, 1000)
        ax2.get_xaxis().set_visible(False)        
        ax2.get_yaxis().set_visible(False)
    
#        ax3 = self.fig.add_subplot(2, 2, 3)
#        ax3.set_xlim(0, 15)
#        ax3.get_yaxis().set_visible(False)
#        ax3.set_ylim(-2, 5)

        return ax1, ax2

    def data_setup(self):

        beams = [
                self.axes[0].plot([], [])[0], 
                self.axes[0].plot([], [], 'r')[0], 
                self.axes[0].plot([], [], 'r')[0], 
                self.axes[1].plot([], [], 'r.')[0], 
                self.axes[1].plot([], [], 'r.')[0], 
                self.axes[1].plot([], [], 'y.')[0], 
                self.axes[1].plot([], [], 'ro')[0]
                ]

        return beams

    def init_data(self):

        for line in self.beams:
            line.set_data([], [])

        return self.beams

    # Animation function
    def animate(self, t):
#        t = t*4 # This gets it to one cycle per second.

        # Obtain data for plotting.
        data = self.information.timestep(t)
        e_data = self.information.e_plot(data[0])
        p_data = self.information.p_plot(data[1]) ############## Tried to change this but failed - new attempt needed
        detector_data = p_data[:,1].tolist()
        time = [t,t]

        if t < 1000:
            if detector_data[0] == 0:
                self.other_data[0].append(detector_data[0])
                self.other_data[1].append(t)
            elif detector_data[1] == 0:
                self.other_data[0].append(detector_data[1])
                self.other_data[1].append(t)
    
        if t < 1000 and t % 10 == 0:
            self.other_data[2].append(detector_data)
            self.other_data[3].append(time)

        beams = self.init_data()
        # Set data for electron beam.
        beams[0].set_data(self.positions.positions(), e_data)
    
        # Set data for two photon beams.
        for line, x, y in zip([beams[1],beams[2]], self.positions.locate_photonbeam(), p_data):
            line.set_data(x,y)

        # Set data for photon beam at detector.
        beams[3].set_data(detector_data, [10,10])
        beams[4].set_data(detector_data, time)
        beams[5].set_data(self.other_data[2], self.other_data[3])
        beams[6].set_data(self.other_data[0], self.other_data[1])
    
    
        return beams

    
    def show_plot(self):

        # Create animations
        anim = animation.FuncAnimation(self.fig, self.animate, init_func=self.init_data,
                                       frames=1000, interval=20, blit=True)
        # Plot positions of kickers and IDs.
        for i in self.positions.locate_devices()[0]:
            self.fig_setup()[0].axvline(x=i, color='k', linestyle='dashed')
        for i in self.positions.locate_devices()[1]:
            self.fig_setup()[0].axvline(x=i, color='r', linestyle='dashed')


        plt.show()


#if __name__ == '__main__':
#    Create_plots().show_plot()


# Initial attempt at adding GUI to control the simulation.


class Control(QtGui.QMainWindow):

    def __init__(self):
        super(Control, self).__init__()
        self.initUI()
        self.plots = Plot()

    def initUI(self):

        QtGui.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        btn = QtGui.QPushButton("Plot",self)
        btn.clicked.connect(self.plotgraphs)
        # then add extra buttons to adjust things

        k3Button = QtGui.QPushButton("K3 +",self)
        k3Button.clicked.connect(self.k3plus)
        k3Button.move(100, 0)

        k3Button = QtGui.QPushButton("K3 -",self)
        k3Button.clicked.connect(self.k3minus)
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
        return self.plots.show_plot()

    def k3plus(self):
        self.plots.information.magnets.step_k3_plus(0.1)

    def k3minus(self):
        self.plots.information.magnets.step_k3_minus(0.1)

    def centre(self):
        
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = Control()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


