#matrices

import dls_packages
import numpy as np


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

	def increment(ds, e):
		drift = np.array([[1,ds],
				  [0,1]])
		return np.dot(drift,e)

class kicker:
	def __init__(self,k,e):
		self.k = k
		self.e = e

	def dipole(k, e):
		kick = np.array([0, k])
		return e + kick

class ID:
	def __init__(self,e):
		self.e = e
	def where:
		return e

#initialise time step
t0 = 0

while True:

	dt = t0%100

	#strength k of magnet varies by sin function
	strength = [np.sin(dt*np.pi/100), np.sin(dt*np.pi/100), 1, np.sin(dt*np.pi/100+np.pi), np.sin(dt*np.pi/100+np.pi)]

	if dt == 0:
		e = e0
	move  = drifting.increment(ds,e)
	path = [kicker.dipole(strength[0],e),move,move,kicker.dipole(strength[1],e),move,ID.where(e),move,kicker.dipole(strength[2],e),move,ID.where(e),move,kicker.dipole(strength[3],e),move,move,kicker.dipole(strength[4],e)]
	for i in path:
		e = path[i]
	print e





