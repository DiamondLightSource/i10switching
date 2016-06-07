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

#how to include ID!

#initialise time step
t0 = 0

for dt in range(10): #while True:

	#dt = t0%100

	#strength k of magnet varies by sin function
	strength = [np.sin(dt*np.pi/10), -(1.5)*np.sin(dt*np.pi/10), 0.5, -(1.5)*(np.sin(dt*np.pi/10+np.pi)+1), np.sin(dt*np.pi/10+np.pi)+1] #currently the kicks aren't right - need to work out what to do :)

	eBeam = e0

	#path of electron beam
	#start
	x = [eBeam[0]]
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

	plt.plot(x)
	plt.show()

	dt += 1


