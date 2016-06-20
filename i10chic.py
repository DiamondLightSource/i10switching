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


    def __init__(self):
        pass # Do I want to have a value of step in here? Apparently yes but couldn't get code to work when I tried to put it in so leaving it for now
        #self.step = None

    def set_length(self, step):
        self.step = step

    def increment(self, e):
        drift = np.array([[1,self.step],
                          [0,1]])
        return np.dot(drift,e)

    def get_type(self):
        return 'drift'


class Kicker:


    def __init__(self):
        pass
        #self.k = None

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


# Define positions of stuff in system
length = [2,1,8,6,4,9,3,7] # lengths to drift between kickers and IDs
pos = [0]
pos.extend(np.cumsum(length))

# Positions of kickers, IDs and 'on axis' photon beam points for plotting purposes.
kicker_pos = [pos[1],pos[2],pos[4],pos[6],pos[7]]
id_pos = [pos[3],pos[5]]
p_pos = [[pos[3], pos[3]+30],[pos[5],pos[5]+30]]

# Define magnet strength factors (dependent on relative positions and time).
len1 = kicker_pos[1] - kicker_pos[0]
len2 = kicker_pos[2] - kicker_pos[1]
d12 = float(len1)/float(len2)
len3 = kicker_pos[3] - kicker_pos[2]
len4 = kicker_pos[4] - kicker_pos[3]
d34 = float(len3)/float(len4)
max_kick = np.array([1, 1 + d12, 2*d12, d12*(1+d34), d12*d34])

# Define time-varying strengths of kicker magnets.
def calculate_strengths(t):

    kick = max_kick*np.array([
        np.sin(t*np.pi/100) + 1, -(np.sin(t*np.pi/100) + 1), 
        1, np.sin(t*np.pi/100) - 1,
        -np.sin(t*np.pi/100) + 1
        ])

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

# Function that returns all objects of a particular type.
def get_elements(path, which):
    objects = []
    for p in path:
        if p.get_type() == which:
            objects.append(p)
    return objects

# Send electron vector through chicane magnets at time t.
def timestep(t):

    # Initialise electron beam
    e_beam = np.array([0,0])
    e_vector = [[0,0]] #[e_beam.tolist()]

    # Initialise photon beam
    p_vector = []

    # Calculate positions of electron beam and photon beam relative to main axis
    for kicker, strength in zip(get_elements(path, 'kicker'), calculate_strengths(t)):
         kicker.set_strength(strength)
    for drift, dist in zip(get_elements(path, 'drift'), length):
         drift.set_length(dist)
    for p in path:
         e_beam = p.increment(e_beam)
         if p.get_type() == 'drift':  # Better way of doing this??
             e_vector.append(e_beam.tolist())  # Allow electron vector to drift and append its new location and velocity to vector collecting the data
         if p.get_type() == 'id':
            p_vector.append(e_beam.tolist())  # Electron vector passes through insertion device, photon vector created

    return e_vector, p_vector, # returns positions and velocities of electrons and photons

'''
#columns testing
f = np.array(timestep(3)[1])
print f
print f[:,0]
print f[:,0][0]
'''

# Extract electron beam positions for plotting.
def e_plot(t):

    e_positions = np.array(timestep(t)[0])[:,0].tolist()

    return e_positions

# Allow the two photon vectors to drift over large distance 
# (ie off the graph) and add the vector for new position and 
# velocity to original vector to create beam for plotting.
def p_plot(t):
    
    p_beam = timestep(t)[1]
    travel = Drifting()
    travel.set_length(p_pos[0][1]-p_pos[0][0])

    for vector in p_beam:
        vector.extend(travel.increment(vector))

    p_beam_array = np.array(p_beam)
    p_positions = p_beam_array[:,[0,2]]

    return p_positions


# Set up figure, axis and plot element to be animated.
fig = plt.figure()
ax = plt.axes(xlim=(0, sum(length)), ylim=(-2, 3))
#e_line, = ax.plot([], [], lw=1)
p_beam = [plt.plot([], [], 'r-')[0] for j in range(2)]

# Initialisation function: plot the background of each frame.
def init():

#    e_line.set_data([], [])
    for line in p_beam:
        line.set_data([], [])
    
    return p_beam #e_line, 

import gc  # This can't stay here! This is garbage collection

# Animation function
def animate(t):

#    e_data = e_plot(t)
    p_data = p_plot(t)
#    e_line.set_data(pos, e_data)
    for line, x, y in zip(p_beam, p_pos, p_data):
        line.set_data(x,y)
#    p_beam.set_data([p_pos[0],p_pos[1]],[p_data[0],p_data[1]])

    gc.collect(0)

    return p_beam #e_line, #WORKED OUT HOW TO PLOT BOTH PHOTON LINES IN A LIST, NOW ADD ELECTRON BEAM DATA TO THAT LIST TOO...


# Call the animator
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

# Plot positions of kickers and IDs
for i in kicker_pos:
    plt.axvline(x=i, color='k', linestyle='dashed')
plt.plot(id_pos, [0,0], 'r.')


plt.show()


