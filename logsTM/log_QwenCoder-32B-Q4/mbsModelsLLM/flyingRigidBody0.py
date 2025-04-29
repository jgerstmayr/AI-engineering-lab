# ** given model description: **
# A free flying rigid body with brick-shape, density = 150 kg/m^3, and xyz-dimensions
# of the cuboid lx=4m, wy=1.2m, hz=1.25m is investigated. The COM of the body
# is initially located at [0,0,0]. The initial velocity shall be [1,4,1.25]
# and the initial angular velocity is [2,1.25,0.8]. Gravity g = 9.81 m/s^2 acts
# in negative x-direction. Contact with ground is not considered and no further
# forces act on the point mass.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
#Create a ground object at given (optional) referencePosition.  Even several ground objects at specific positions can be added.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a brick (cuboid) shape; uses rotated reference configuration.
lx = 4
wy = 1.2
hz = 1.25

#create inertia instance for cuboid (brick) shape
density = 150 #kg/m^3
volume = lx * wy * hz
inertiaCube = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])
inertiaCube = inertiaCube.Translated([0,0,0]) #translate COM (in body-frame), only if needed

#create a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [0,0,0], #reference position, not COM
                             referenceRotationMatrix = RotationVector2RotationMatrix([0,0,0]),
                             initialAngularVelocity = [2,1.25,0.8],
                             initialVelocity = [1,4,1.25],
                             gravity = [-9.81,0,0])

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-2
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3

#start solver:
mbs.SolveDynamic(simulationSettings)

