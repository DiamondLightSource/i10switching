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


# Define positions of devices in system
lengths = [2,2,4,4,4,4,2,20] # lengths to drift between kickers and IDs
kicker3 = 1


class Locate:


    def __init__(self, lengths):
        self.lengths = lengths

    def locate_devices(self):
        
        positions = [0]
        positions.extend(np.cumsum(self.lengths))
    
        return positions

    def locate_kicker(self):

        kicker_pos = [self.locate_devices()[1],self.locate_devices()[2],self.locate_devices()[4],self.locate_devices()[6],self.locate_devices()[7]]

        return kicker_pos

    def locate_id(self):

        id_pos = [self.locate_devices()[3],self.locate_devices()[5]]

        return id_pos

    def locate_detector(self):

        return self.locate_devices()[8]

    def locate_photonbeam(self):

        p_pos = [[self.locate_id()[0], self.locate_detector()],[self.locate_id()[1],self.locate_detector()]]

        return p_pos


# Define magnet strength factors (dependent on relative positions and time).
def max_magnet_strengths():

    kicker_pos = Locate(lengths).locate_kicker()
    len1 = kicker_pos[1] - kicker_pos[0]
    len2 = kicker_pos[2] - kicker_pos[1]
    d12 = float(len1)/float(len2)
    len3 = kicker_pos[3] - kicker_pos[2]
    len4 = kicker_pos[4] - kicker_pos[3]
    d34 = float(len3)/float(len4)
    max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34]) 

    return max_kick

# Define time-varying strengths of kicker magnets.
def calculate_strengths(t):

    max_kick = max_magnet_strengths()
    graphscale = 0.5
    kick = graphscale*max_kick*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        kicker3, np.sin(t*np.pi/100) - 1,
        -np.sin(t*np.pi/100) + 1
        ]) # Factor 0.5 so that maximum kick applied = 1.

    return kick

# Define path through system.
path = [
    Drifting(),Kicker(),
    Drifting(),Kicker(),
    Drifting(),InsertionDevice(),
    Drifting(),Kicker(),
    Drifting(),InsertionDevice(),
    Drifting(),Kicker(),
    Drifting(),Kicker(),
    Drifting()
    ]

# Function that returns all objects of a particular type from path.
def get_elements(path, which):
    list_objects = []
    for p in path:
        if p.get_type() == which:
            list_objects.append(p)
    return list_objects

# Set drift distances (time independent).
for drift, distance in zip(get_elements(path, 'drift'), lengths):
    drift.set_length(distance)

# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam position and velocity
    e_beam = np.array([0,0])
    e_vector = [[0,0]]

    # Initialise photon beam position and velocity
    p_vector = []

    # Calculate positions of electron beam and photon beam relative to main axis.
    for kicker, strength in zip(get_elements(path, 'kicker'), calculate_strengths(t)):
         kicker.set_strength(strength)
    for p in path:
         e_beam = p.increment(e_beam)
         device = p.get_type()
         if device == 'drift':  # Better way of doing this?? # list for x and y positions then can remove duplicates after
             e_vector.append(e_beam.tolist())  # Allow electron vector to drift and append its new location and velocity to vector collecting the data
         elif device == 'id':
            p_vector.append(e_beam.tolist())  # Electron vector passes through insertion device, photon vector created

    return e_vector, p_vector # returns positions and velocities of electrons and photons


# Extract electron beam positions for plotting.
def e_plot(e_beam):

    e_positions = np.array(e_beam)[:,0]

    return e_positions

# Allow the two photon vectors to drift over large distance 
# and add the vector for new position and velocity to 
# original vector to create beam for plotting.
def p_plot(p_beam):
    
    travel = [Drifting(),Drifting()]
    p_pos = Locate(lengths).locate_photonbeam()
    for i in range(2):
        travel[i].set_length(p_pos[i][1]-p_pos[i][0])
        p_beam[i].extend(travel[i].increment(p_beam[i]))

    p_positions = np.array(p_beam)[:,[0,2]]

    return p_positions

####################
## Graph plotting ##
####################
# PUT THIS ALL INTO A CLASS

'''
class Plotting:

    def __init__(self):
        pass

    def fig(self):
    
        fig = plt.figure()
        ax1 = fig.add#....
        #etc

    def init():

        for line in beams:
            line.set_data([], [])

        return beams #where do we get beams from??

    def animate(data):

        # put whole animate function in here
        # but where call t? pass t to animate??
        # no actually pass data to animate where data = timestep(t) has already been done...


# do some stuff here to work out

#eventually call animate something like this:

anim = animation.FuncAnimation(Plotting().fig(), Plotting().animate(data), init_func=Plotting().init(),
                               frames=1000, interval=20, blit=True)

#have a function which calls timestep(t) to get data and then uses this in anim

def do_the_animation():
    data = timestep(t) #BUT WHERE DOES T COME FROM? NEEDS A BIT MORE THOUGHT


'''

# Set up figure, axis and plot element to be animated.
fig = plt.figure()

ax1 = fig.add_subplot(2, 1, 1)
ax1.set_xlim(0, sum(lengths))
ax1.set_ylim(-2, 5)

ax2 = fig.add_subplot(2, 2, 3)
ax2.set_xlim(-10, 10)
ax2.set_ylim(0, 10)

ax3 = fig.add_subplot(2, 2, 4)
ax3.set_xlim(-10, 10)
ax3.set_ylim(0, 1000)

beams = [ax1.plot([], [])[0], ax1.plot([], [], 'r')[0], 
         ax1.plot([], [], 'r')[0], ax3.plot([], [], 'r.')[0], 
         ax3.plot([], [], 'r.')[0], ax3.plot([], [], 'y.')[0], 
         ax3.plot([], [], 'ro')[0]]


# Initialisation function: plot the background of each frame.
def init():

    for line in beams:
        line.set_data([], [])

    return beams

import gc  # This can't stay here! This is garbage collection

detector_flash = []
detector_flash_time = []
flash2 = [] # Extra - to be tidied up
ftime2 = []

# Animation function
def animate(t):

    # Obtain data for plotting.
    data = timestep(t)
    e_data = e_plot(data[0])
    p_data = p_plot(data[1])
    detector_data = p_data[:,1].tolist()
    if t < 1000:
        if detector_data[0] == 0:
            detector_flash.append(detector_data[0])
            detector_flash_time.append(t)
        elif detector_data[1] == 0:
            detector_flash.append(detector_data[1])
            detector_flash_time.append(t)
    time = [t,t]

    if t < 1000 and t % 10 == 0:
        flash2.append(detector_data)
        ftime2.append(time)

    # Set data for electron beam.
    beams[0].set_data(Locate(lengths).locate_devices(), e_data)

    # Set data for two photon beams.
    for line, x, y in zip([beams[1],beams[2]], Locate(lengths).locate_photonbeam(), p_data):
        line.set_data(x,y)

    # Set data for photon beam at detector.
    beams[3].set_data(detector_data, [10,10])
    beams[4].set_data(detector_data, time)
    beams[5].set_data(flash2, ftime2) # Some extra plotting as a guide to the eye.
    beams[6].set_data(detector_flash, detector_flash_time)

    gc.collect(0)

    return beams


# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=1000, interval=20, blit=True)

# Plot positions of kickers and IDs.
for i in Locate(lengths).locate_kicker():
    ax1.axvline(x=i, color='k', linestyle='dashed')
for i in Locate(lengths).locate_id():
    ax1.axvline(x=i, color='r', linestyle='dashed')




plt.show()


