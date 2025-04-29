# ** given model description: **
# Free-fall motion of an object with the following properties: point mass
# m = 1.5 kg, gravity g = 9.81 m/s^2 (in negative z-direction). The object
# starts from rest and is dropped from a height hz = 20 m. The free fall shall be
# analyzed for 1 s. Air resistance is neglected and except the action of gravity,
# no forces act on the point mass..
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import  *
import numpy as np

#set up new multibody system to work with
SC  = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
#Create a ground object at given (optional) referencePosition.  Even several ground objects at specific positions can be added.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a point mass object with specified mass at reference position with optional initial conditions
#physicsMass: the mass in kg
#referencePosition: initial/reference position at which mechanism is defined; 
#initialDisplacement: additional initial deviations from referencePosition; usually this is [0,0,0]
#initialVelocity: initial velocities of mass point
#all vectors always have 3 components, no matter if 2D or 3D problem
oMass = mbs.CreateMassPoint(physicsMass=1.5, referencePosition=[0,0,20], 
                            initialDisplacement=[0,0,0],   #optional, relative to reference position
                            initialVelocity=[0,0,0],     #optional
                            gravity=[0,0,-9.81])           #optional

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1


#start solver:
mbs.SolveDynamic(simulationSettings)


