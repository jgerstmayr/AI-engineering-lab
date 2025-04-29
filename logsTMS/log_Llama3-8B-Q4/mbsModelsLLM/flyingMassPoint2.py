# ** given model description: **
# Projectile motion of a point mass with the following properties: mass m
# = 10  kg, gravity g = 9.81 m/s^2, initial velocity in x/y/z-direction: vx
# = 5 m/s, vy = 10 m/s, vz = 0 m/s. The initial position is given as x=0 and
# y=0. Gravity acts along the negative y-axis, and there is no other external
# propulsion or resistance. The motion shall be evaluated for 1 s. Contact with ground
# is not modelled, so the projectile can go below y=0. Except the action of
# gravity, no forces act on the point mass.
import exudyn as exu
from exudyn.utilities import *
import numpy as np

SC = exu.SystemContainer()
mbs = SC.AddSystem()

oGround = mbs.CreateGround(referencePosition=[0,0,0])

oMass = mbs.CreateMassPoint(physicsMass=10, referencePosition=[0,0,0], 
                            initialDisplacement=[0,0,0], 
                            initialVelocity=[5,10,0], 
                            gravity=[0,-9.81,0])

mbs.Assemble()

tEnd = 1
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=0.1


#start solver:
mbs.SolveDynamic(simulationSettings)


