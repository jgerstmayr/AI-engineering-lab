# ** given model description: **
# Rotational motion of a spinning disc (around z-axis) with the following
# properties: mass m = 15 kg, disc radius r = 0.25 m, disc width w = 0.025, and initial
# angular velocity omega_z = 30 rad/s. The disc is mounted on a frictionless revolute
# joint and experiences a constant torque T_z = 0.8. No gravity acts on the disc.
#import Exudyn library and utilities
import exudyn as exu
from exudyn.utilities import *
import numpy as np

#set up new multibody system to work with
SC = exu.SystemContainer()
mbs = SC.AddSystem()

#Create a ground object as an inertial reference frame for the multibody system.
oGround = mbs.CreateGround(referencePosition=[0,0,0])

#Create a rigid body with a cylindrical shape.
mass = 15 
outerRadius = 0.25
length = 0.025
volume = np.pi * outerRadius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=outerRadius, axis=2)

#create a free rigid body using the defined inertia properties and applies gravity (y-direction).
oBody = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0,0,0], #reference position x/y/z of COM
                            initialVelocity=[0,0,0],   #optional
                            initialAngularVelocity=[0,0,30], #optional
                            gravity=[0,0,0])       #optional

#Applies a 3D torque to a rigid body.
#torque of 0.8Nm around the z-axis:
mbs.CreateTorque(bodyNumber=oBody, loadVector=[0,0,0.8]) #torque of 0.8Nm around z-axis

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


