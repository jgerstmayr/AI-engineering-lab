# ** given model description: **
# Pendulum modeled with a brick-shape rigid body and a revolute joint. The
# body has density = 1200 kg/m^3, and xyz-dimensions lx=2m, wy=0.12m, hz=0.12m.
# The center of mass is equal to the reference point and initially located at
# [lx/2,0,0], while the revolute joint (rotation around z-axis) is located at [0,0,0]
# (global coordinates). Gravity g = 9.81 m/s^2 acts in negative y-direction, and
# no further force acts.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a brick (cuboid) shape.
rbX = 2
rbY = 0.12
rbZ = 0.12

#create inertia instance for cuboid (brick) shape
mass = rbX * rbY * rbZ * 1200 #kg
volume = rbX * rbY * rbZ
inertiaCube = InertiaCuboid(density=mass/volume, sideLengths=[rbX, rbY, rbZ])

#create a free rigid body with defined inertia and applies gravity.
oBody = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [rbX/2,0,0], #reference position, not COM
                             initialVelocity = [0,0,0],   #optional
                             initialAngularVelocity = [0,0,0], #optional
                             gravity = [0,-9.81,0])

#Create a revolute joint between two rigid bodies / ground, allowing rotation about a specified axis; not compatible with point mass.
mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oBody], 
                        position=[0,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        useGlobalFrame=True)

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


