# i10chic.py
# Animated simulation of chicane magnets

# Import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Define matrices to modify the electron beam vector:
# drift, kicker magnets, insertion devices.

class Drifting:


    def __init__(self, step=0):
        self.step = step

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def get_type(self):
        return 'drift'



class Kicker:


    def __init__(self, k=0):
        self.k = k

    def set_strength(self, k):
        self.k = k

    def increment(self, e):
        kick = np.array([0, self.k])
        return e + kick

    def get_type(self):
        return 'kicker'


class InsertionDevice:


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def get_type(self):
        return 'id'

# Assign the values of constants in the system:
# distances between devices and strength of 3rd kicker.

class Constants:

    def __init__(self):
        self.length_list = [2,2,4,4,4,4,2,20]
        self.kicker3_strength = 1

    def lengths(self):

        return self.length_list

    def kicker3(self):

        return self.kicker3_strength

# Assign locations of devices along the axis of the system.

class Locate:


    def __init__(self, lengths):
        self.lengths = lengths

    def locate_devices(self):
        
        positions = [0]
        positions.extend(np.cumsum(self.lengths))
    
        return positions

    def locate_kicker(self):

        kicker_pos = [self.locate_devices()[1],
                      self.locate_devices()[2],
                      self.locate_devices()[4],
                      self.locate_devices()[6],
                      self.locate_devices()[7]]

        return kicker_pos

    def locate_id(self):

        id_pos = [self.locate_devices()[3],self.locate_devices()[5]]

        return id_pos

    def locate_detector(self):

        d_pos = self.locate_devices()[8]

        return d_pos

    def locate_photonbeam(self):

        p_pos = [[self.locate_id()[0], self.locate_detector()],
                 [self.locate_id()[1], self.locate_detector()]]

        return p_pos

# Collect data on electron and photon beams at time t.

class Collect_data:

    def __init__(self):
        self.path = [
                    Drifting(),Kicker(),
                    Drifting(),Kicker(),
                    Drifting(),InsertionDevice(),
                    Drifting(),Kicker(),
                    Drifting(),InsertionDevice(),
                    Drifting(),Kicker(),
                    Drifting(),Kicker(),
                    Drifting()
                    ]
    #PUT THIS IN A FUNCTION? OR CLASS?
    # Set drift distances (time independent).
        for drift, distance in zip(self.get_elements('drift'), Constants().lengths()):
            drift.set_length(distance)

    # Define magnet strength factors (dependent on relative positions and time).
    def max_magnet_strengths(self):

        kicker_pos = Locate(Constants().lengths()).locate_kicker()
        len1 = kicker_pos[1] - kicker_pos[0]
        len2 = kicker_pos[2] - kicker_pos[1]
        d12 = float(len1)/float(len2)
        len3 = kicker_pos[3] - kicker_pos[2]
        len4 = kicker_pos[4] - kicker_pos[3]
        d34 = float(len3)/float(len4)
        max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 
    
        return max_kick
    
    # Define time-varying strengths of kicker magnets.
    def calculate_strengths(self,t):
    
        max_kick = self.max_magnet_strengths()
        graphscale = 0.5
        kicker3 = Constants().kicker3()
        kick = graphscale*max_kick*np.array([
            np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
            kicker3, np.sin(t*np.pi/100) - 1,
            -np.sin(t*np.pi/100) + 1
            ])
    
        return kick

    # Function that returns all objects of a particular type from path.
    def get_elements(self, which):
        list_objects = []
        for p in self.path:
            if p.get_type() == which:
                list_objects.append(p)
        return list_objects
    
    # Send electron vector through chicane magnets at time t.
    def timestep(self,t):
    
        # Initialise electron beam position and velocity
        e_beam = np.array([0,0])
        e_vector = [[0,0]]
    
        # Initialise photon beam position and velocity
        p_vector = []
    
        # Calculate positions of electron beam and photon beam relative to main axis.
        for kicker, strength in zip(self.get_elements('kicker'), self.calculate_strengths(t)):
             kicker.set_strength(strength)
        for p in self.path:
             e_beam = p.increment(e_beam)
             device = p.get_type()
             if device == 'drift':  # Better way of doing this?? # list for x and y positions then can remove duplicates after #TO DO ########################################################
                 e_vector.append(e_beam.tolist())  # Allow electron vector to drift and append its new location and velocity to vector collecting the data
             elif device == 'id':
                p_vector.append(e_beam.tolist())  # Electron vector passes through insertion device, photon vector created
    
        return e_vector, p_vector # returns positions and velocities of electrons and photons
    
    
    # Extract electron beam positions for plotting.
    def e_plot(self,e_beam):
    
        e_positions = np.array(e_beam)[:,0]
    
        return e_positions
    
    # Allow the two photon vectors to drift over large distance 
    # and add the vector for new position and velocity to 
    # original vector to create beam for plotting.
    def p_plot(self,p_beam):
        
        travel = [Drifting(),Drifting()]
        p_pos = Locate(Constants().lengths()).locate_photonbeam()
        for i in range(2):
            travel[i].set_length(p_pos[i][1]-p_pos[i][0])
            p_beam[i].extend(travel[i].increment(p_beam[i]))
    
        p_positions = np.array(p_beam)[:,[0,2]]
    
        return p_positions


####################
## Graph plotting ##
####################

class Plot_setup:


    def __init__(self, fig):
        self.fig = fig

    def fig_setup(self):

        ax1 = self.fig.add_subplot(2, 1, 1)
        ax1.set_xlim(0, sum(Constants().lengths()))
        ax1.set_ylim(-2, 5)
    
        ax2 = self.fig.add_subplot(2, 2, 3)
        ax2.set_xlim(-10, 10)
        ax2.set_ylim(0, 10)
        
        ax3 = self.fig.add_subplot(2, 2, 4)
        ax3.set_xlim(-10, 10)
        ax3.set_ylim(0, 1000)

        return ax1, ax2, ax3

    def data_setup(self):

        axes = self.fig_setup()

        beams = [axes[0].plot([], [])[0], axes[0].plot([], [], 'r')[0], 
                 axes[0].plot([], [], 'r')[0], axes[2].plot([], [], 'r.')[0], 
                 axes[2].plot([], [], 'r.')[0], axes[2].plot([], [], 'y.')[0], 
                 axes[2].plot([], [], 'ro')[0]]

        return beams


class Plotting:


    def __init__(self,beams,other):
        self.beams = beams
        self.other = other

    def init_data(self):

        for line in self.beams:
            line.set_data([], [])

        return self.beams

    # Animation function
    def animate(self, t):

        # Obtain data for plotting.
        information = Collect_data()
        data = information.timestep(t)
        e_data = information.e_plot(data[0])
        p_data = information.p_plot(data[1])
        detector_data = p_data[:,1].tolist()
        time = [t,t]

        if t < 1000:
            if detector_data[0] == 0:
                self.other[0].append(detector_data[0])
                self.other[1].append(t)
            elif detector_data[1] == 0:
                self.other[0].append(detector_data[1])
                self.other[1].append(t)
    
        if t < 1000 and t % 10 == 0:
            self.other[2].append(detector_data)
            self.other[3].append(time)

        beams = self.init_data()
        positions = Locate(Constants().lengths())
        # Set data for electron beam.
        beams[0].set_data(positions.locate_devices(), e_data) #prob only want to call classes once
    
        # Set data for two photon beams.
        for line, x, y in zip([beams[1],beams[2]], positions.locate_photonbeam(), p_data):
            line.set_data(x,y)

        # Set data for photon beam at detector.
        beams[3].set_data(detector_data, [10,10])
        beams[4].set_data(detector_data, time)
        beams[5].set_data(self.other[2], self.other[3]) # Some extra plotting as a guide to the eye.
        beams[6].set_data(self.other[0], self.other[1])
    
    
        return beams


class Create_plots(object):


    def __init__(self): 

        self.fig = plt.figure()
        self.other_data = [[],[],[],[]]

        setup = Plot_setup(self.fig)
        self.axes = setup.fig_setup()
        self.data = setup.data_setup()
        self.init = Plotting(self.data, self.other_data).init_data
        
    def show_plot(self):

        # Create animations
        anim = animation.FuncAnimation(self.fig, Plotting(self.data, self.other_data).animate, init_func=self.init,
                                       frames=1000, interval=20, blit=True)
        # Plot positions of kickers and IDs.
        for i in Locate(Constants().lengths()).locate_kicker():
            self.axes[0].axvline(x=i, color='k', linestyle='dashed')
        for i in Locate(Constants().lengths()).locate_id():
            self.axes[0].axvline(x=i, color='r', linestyle='dashed')

        plt.show()


if __name__ == '__main__':
    Create_plots().show_plot()








