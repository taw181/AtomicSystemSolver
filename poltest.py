from qobjects import Laser
from qutipfuncs import pol

Bdir = [0, 0, 1]

laser_p = Laser(S=[1, 0, 0])
laser_m = Laser(S=[-1, 0, 0])
laser_pi = Laser(k=90, S=[1, 0, 0])

print(pol(laser_p, Bdir))
print(pol(laser_m, Bdir))
print(pol(laser_pi, Bdir))
