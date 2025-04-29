# ** given model description: **
# Double pendulum modeled with brick-shape rigid bodies and revolute joints.
# Both bodies have density = 2500 kg/m^3, and xyz-dimensions lx=0.8 m, wy=0.2
# m, hz=0.2 m. The first body's center is located initially at [lx/2,0,0] and
# the second body at [3*lx/2,0,0], both bodies having their COM locally at [0,0,0]
# (not translated). The first revolute joint between ground and body 1 is located
# at [0,0,0] (global coordinates), and the second revolute joint between body
# 1 and body 2 is located at [lx,0,0] (global coordinates). Both revolute joints'
# have a free rotation around the z-axis.Gravity g = 9.81 m/s^2 acts in negative
# y-direction, and no further force acts.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#xyz-dimensions of the brick-shape rigid bodies
lx = 0.8
wy = 0.2
hz = 0.2

#density of the bodies
density = 2500

#volume of the bodies
volume = lx * wy * hz

#inertia instance for cuboid (brick) shape
inertiaCube = InertiaCuboid(density=density, sideLengths=[lx, wy, hz])

#first rigid body
oBody1 = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,0,0],   #optional
                             initialAngularVelocity = [0,0,0], #optional
                             gravity = [0,-9.81,0])

#second rigid body
oBody2 = mbs.CreateRigidBody(inertia = inertiaCube,
                             referencePosition = [3*lx/2,0,0], #reference position, not COM
                             initialVelocity = [0,0,0],   #optional
                             initialAngularVelocity = [0,0,0], #optional
                             gravity = [0,-9.81,0])

#first revolute joint between ground and body 1
mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oBody1], 
                        position=[0,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        useGlobalFrame=True)

#second revolute joint between body 1 and body 2
mbs.CreateRevoluteJoint(bodyNumbers=[oBody1, oBody2], 
                        position=[lx,0,0], #global position of joint
                        axis=[0,0,1], #rotation along global z-axis
                        useGlobalFrame=True)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.001

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 1e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3


#start solver:
mbs.SolveDynamic(simulationSettings)


