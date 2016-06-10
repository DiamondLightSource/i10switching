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


    def __init__(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def type(self):
        return 'drift'


class Kicker:


    def __init__(self, which):
        self.which = which

    def identify(self):
        return self.which

    def increment(self, e, k):
        kick = np.array([0, k])
        return e + kick

    def type(self):
        return 'kicker'


class InsertionDevice:


    def __init__(self):
        pass

    def increment(self, e):
        return e

    def type(self):
        return 'id'


# Define positions of stuff in system
length = [2,1,8,6,4,9,3,7] # lengths to drift between kickers and IDs
pos = [0]
pos.extend(np.cumsum(length))

# Positions of kickers, IDs and 'on axis' photon beam points for plotting purposes.
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]]
p_pos = [[pos[3], pos[3]+30],[pos[5],pos[5]+30]]

# Define magnet strength factors (dependent on relative positions and time).
len1 = pos[2] - pos[1]
len2 = pos[4] - pos[2]
d12 = float(len1)/float(len2)
len3 = pos[6] - pos[4]
len4 = pos[7] - pos[6]
d34 = float(len3)/float(len4)
stren = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34])

def strength(t):

    kick = stren*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, np.sin(t*np.pi/100) - 1,
        -np.sin(t*np.pi/100) + 1
        ])

    return kick

# Define path through system.
path = [
    Drifting(length[0]),Kicker(0),
    Drifting(length[1]),Kicker(1),
    Drifting(length[2]),InsertionDevice(),
    Drifting(length[3]),Kicker(2),
    Drifting(length[4]),InsertionDevice(),
    Drifting(length[5]),Kicker(3),
    Drifting(length[6]),Kicker(4),
    Drifting(length[7])
    ]
#function that returns all items in order of particular type so don't have to check if it's a kicker when going through

def get_elements(path):
    drifts = []
    kickers = []
    ids = []
    for p in path:
        which = p.type()
        if which == 'drift':
            drifts.append(p)
        elif which == 'kicker':
            kickers.append(p)
        elif which == 'id':
            ids.append(p)
    return drifts, kickers, ids # This doesn't do what I want it to do yet. What do I want it to do?

print get_elements(path)[0][0].type()

# Take path element, find out what element it is, apply relevant action

# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam
    e_beam = np.array([0,0])
    e_loc = [e_beam[0]]
    e_vector = [0,0] # this currently doesn't do anything - need to work out how to use

    # Initialise photon beam
    p_vector = []

    # Calculate positions of electron beam and photon beam relative to main axis
    kick = strength(t)
    for p in path:
        if p.type() == 'kicker':
            e_beam = p.increment(e_beam,kick[p.identify()])  # Apply kick to electron beam
        elif p.type() == 'drift':
            e_beam = p.increment(e_beam)
            e_loc.append(e_beam[0])
            e_vector.append([e_beam[0],e_beam[1]])  # Allow electron vector to drift and append its new location and velocity to vector collecting the data #must be a nicer way to append this data...
        elif p.type() == 'id':
            e_beam = p.increment(e_beam)
            p_vector.append([e_beam[0],e_beam[1]])  # Electron vector passes through insertion device, photon vector created
    
    return e_vector, p_vector, e_loc  # returns positions and locations but currently just using positions STILL NEEDS SOME TIDYING
'''
#columns testing
f = np.array(timestep(3)[1])
print f
print f[:,0]
print f[:,0][0]
'''

# Photon beam data: returns list of beam vector positions and velocity directions
def photon(t):

    photon_beam = timestep(t)[1]
    # Allow photon vector to drift over large distance (ie off the graph)
    # and add the vector describing its new position and velocity to the 
    # information of its original position. For both beams simultaneously.
    for vector in photon_beam:
        vector.extend(Drifting(p_pos[0][1]-p_pos[0][0]).increment(vector))

    return photon_beam

# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 3))
e_line, = ax.plot([], [], lw=1)
p_beam1, = ax.plot([], [], 'r-')
p_beam2, = ax.plot([], [], 'r-')

# Initialisation function: plot the background of each frame.
def init():

    e_line.set_data([], [])
    p_beam1.set_data([], [])
    p_beam2.set_data([], [])
    
    return e_line, p_beam1, p_beam2,

import gc  # This can't stay here! This is garbage collection

# Animation function
def animate(t):

    e_data = timestep(t)[2] # NEEDS SORTING OUT
    p_data = photon(t)
    e_line.set_data(pos, e_data)
    p_beam1.set_data(p_pos[0],[p_data[0][0],p_data[0][2]])
    p_beam2.set_data(p_pos[1],[p_data[1][0],p_data[1][2]]) # I'm resetting the data each time but not sure I can do a multiple plot thing with the way the photon data is currently set up...
    gc.collect(0)

    return e_line, p_beam1, p_beam2,

# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

# Plot positions of kickers and IDs
for i in kicker_pos:
    plt.axvline(x=i, color='k', linestyle='dashed')
plt.plot(id_pos, [0,0], 'r.')


plt.show()


