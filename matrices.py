# matrices.py
# animated simulation of chicane magnets

# import libraries

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# define matrices to modify the electron beam vector - drift and kicker magnets

class drifting:
	def __init__(self,ds,e):
		self.ds = ds
		self.e = e

	def increment(self):
		drift = np.array([[1,self.ds],
				  [0,1]])
		return np.dot(drift,self.e)

class kicker:
	def __init__(self,k,e):
		self.k = k
		self.e = e

	def dipole(self):
		kick = np.array([0, self.k])
		return self.e + kick

# define the insertion device - this isn't currently used and needs to be added

class ID:
	def __init__(self,e):
		self.e = e
	def where(self):
		return self.e

# send electron vector through chicane magnets at time t

def timestep(t):
	# initialise electron beam
	eBeam = np.array([0,0])
	eP = [eBeam[0]]

	# set size of step through chicane
	ds = 1

	# strength k of magnets vary by sin function
	strength = [np.sin(t*np.pi/100)+1, -(1.5)*(np.sin(t*np.pi/100)+1), 1, -(1.5)*(np.sin(t*np.pi/100+np.pi)+1), np.sin(t*np.pi/100+np.pi)+1]
	
	# path of electron beam through chicane magnets

	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	# first kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[0],eBeam).dipole()
	eP.append(eBeam[0])
	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	# second kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[1],eBeam).dipole()
	eP.append(eBeam[0])
	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0]) # insertion device here - to be added later
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	# third kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[2],eBeam).dipole()
	eP.append(eBeam[0])
	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0]) # insertion device here - to be added later
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	# fourth kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[3],eBeam).dipole()
	eP.append(eBeam[0])
	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	# fifth kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[4],eBeam).dipole()
	eP.append(eBeam[0])
	# drift
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	eP.append(eBeam[0])

	return eP


# set up figure, axis and plot element to be animated
fig = plt.figure()
ax = plt.axes(xlim=(0, 16), ylim=(-2, 5))
line, = ax.plot([], [], lw=2)

# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    return line,

# animation function
def animate(t):
    x = np.arange(0, 17) # currently just plotting position of electron beam against integers - to be modified
    y = timestep(t)
    line.set_data(x, y)
    return line,

# call the animator.  blit=True means only re-draw the parts that have changed.
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=10, blit=True)

plt.show()






