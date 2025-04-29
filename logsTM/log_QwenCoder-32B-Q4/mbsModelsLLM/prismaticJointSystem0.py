# ** given model description: **
# A system consisting of a brick-shaped rigid body freely moving on a prismatic
# joint in y-direction. The COM of the rigid body is placed at [0,0,0]. The rigid
# body has a mass of m = 8 kg and the side lengths of the body are all equal with
# s = 0.8 m. A force f = 6 N acts on the rigid body's COM in y-direction. Gravity
# is neglected.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a brick (cuboid) shape; uses rotated reference configuration.
rbX = 0.8
rbY = 0.8
rbZ = 0.8

#create inertia instance for cuboid (brick) shape
mass=8 #kg
volume=rbX*rbY*rbZ
inertiaCube = InertiaCuboid(density=mass/volume, sideLengths=[rbX,rbY,rbZ])
inertiaCube = inertiaCube.Translated([0,0,0]) #translate COM (in body-frame), only if needed

#create a free rigid body with defined inertia and applies an initial rotation and velocity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [0,0,0], #reference position, not COM
                             referenceRotationMatrix = RotationVector2RotationMatrix([0,0,0]),
                             initialAngularVelocity = [0,0,0],
                             initialVelocity = [0,0,0],
                             gravity = [0,0,0])

#Applies a force in a specific direction to a rigid body at its local position.
#apply 6N in y-direction:
loadRigidBody = mbs.CreateForce(bodyNumber=oBody, localPosition=[0,0,0], loadVector=[0,6,0])

#Create a prismatic joint between two rigid bodies / ground, allowing linear motion along a specified axis; position and axis are defined in global reference configuration
mbs.CreatePrismaticJoint(bodyNumbers=[oGround, oBody], 
                         position=[0,0,0], #global position of joint
                         axis=[0,1,0], #global axis of joint, can move in global y-direction
                         useGlobalFrame=True) #use local coordinates for joint definition

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 1
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


