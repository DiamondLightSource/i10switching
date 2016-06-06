#matrices

import dls_packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animate


#k = strength of kicker --> amount by which velocity is incremented by kick
#dt = time increment of whole process
#ds = increment for electron vector
ds = 1

#initial position and velocity (along x axis)
e0 = np.array([0,0])

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

#initialise time step
t0 = 0

for dt in range(10): #while True:

	#dt = t0%100

	#strength k of magnet varies by sin function
	strength = [np.sin(dt*np.pi/10), -1.5*np.sin(dt*np.pi/10), 0.5, -1.5*np.sin(dt*np.pi/10+np.pi/2), np.sin(dt*np.pi/10+np.pi/2)] #currently the kicks aren't right - need to work out what to do

	if dt == 0:
		e = e0

	'''
	path = [magnet[0].dipole(), move.increment(), move.increment(), magnet[1].dipole(), move.increment(), insertion.where(), move.increment(), magnet[2].dipole(), move.increment(), insertion.where(), move.increment(), magnet[3].dipole(), move.increment(), move.increment(), magnet[4].dipole()]

	x = [e0[0]]
	for i in range(len(path)):
		e = path[i]
		x.append(e[0])
	print x
	plt.plot(np.arange(16),x)
#	plt.show()
	'''

	#x is velocity
	x = [e0[1]]
	e = kicker(strength[0],e).dipole()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = kicker(strength[1],e).dipole()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = ID(e).where()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = kicker(strength[2],e).dipole()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = ID(e).where()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = kicker(strength[3],e).dipole()
	x.append(e[1])
	e = drifting(ds,e).increment()
	x.append(e[1])
	e = kicker(strength[4],e).dipole()
	x.append(e[1])

	#############

#	print x
	plt.plot(np.arange(14),x)
	plt.show()

	dt += 1

#problem with the kick strengths currently - not getting beam correctly back on track, but at least the beam is following instructions, even if they're wrong! :)



