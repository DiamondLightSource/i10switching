#matrices

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#allow electron to drift between magnets
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

class ID:
	def __init__(self,e):
		self.e = e
	def where(self):
		return self.e

#how to include ID!
#for dt in range(10): #while True:

	#dt = t0%100


def timestep(dt):
	eBeam = np.array([0,0])
	x = [eBeam[0]]
	ds = 1
	#strength k of magnet varies by sin function
	strength = [np.sin(dt*np.pi/10)+1, -(1.5)*(np.sin(dt*np.pi/10)+1), 1, -(1.5)*(np.sin(dt*np.pi/10+np.pi)+1), np.sin(dt*np.pi/10+np.pi)+1]

	#path of electron beam

	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	#first kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[0],eBeam).dipole()
	x.append(eBeam[0])
	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	#second kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[1],eBeam).dipole()
	x.append(eBeam[0])
	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0]) #ID somewhere here - to be added later
	#third kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[2],eBeam).dipole()
	x.append(eBeam[0])
	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0]) #ID somewhere here - to be added later
	#fourth kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[3],eBeam).dipole()
	x.append(eBeam[0])
	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	#fifth kicker
	eBeam = drifting(ds,eBeam).increment()
	eBeam = kicker(strength[4],eBeam).dipole()
	x.append(eBeam[0])
	#drift
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])
	eBeam = drifting(ds,eBeam).increment()
	x.append(eBeam[0])

	return x


# First set up the figure, the axis, and the plot element we want to animate
fig = plt.figure()
ax = plt.axes(xlim=(0, 16), ylim=(-2, 5))
line, = ax.plot([], [], lw=2)

# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    return line,

# animation function.  This is called sequentially
def animate(t):
    x = np.arange(0, 17)
    y = timestep(t)
    line.set_data(x, y)
    return line,

# call the animator.  blit=True means only re-draw the parts that have changed.
anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=200, interval=70, blit=True)

plt.show()






