# ** given model description: **
# Torsional oscillator consisting of a cylindrical disc with rotational motion
# around z-axis and a torsional spring-damper with the following properties: mass
# m = 12 kg, disc radius r = 0.75 m, disc width w = 0.125, torsional stiffness
# k = 2000 Nm/rad, torsional damping coefficient d = 8 Nms/rad and initial
# angular velocity omega_z = 12.5 rad/s. The disc is mounted on a frictionless revolute
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
mass = 12 
outerRadius = 0.75
length = 0.125
volume = np.pi * outerRadius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=outerRadius, axis=2)

#create a free rigid body using the defined inertia properties and no gravity.
oBody = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0,0,0], 
                            initialVelocity=[0,0,0],   
                            initialAngularVelocity=[0,0,12.5], 
                            gravity=[0,0,0])       

#Create a revolute joint between the rigid body and ground, allowing rotation about the z-axis.
mbs.CreateRevoluteJoint(bodyNumbers=[oGround, oBody], 
                        position=[0,0,0], 
                        axis=[0,0,1], 
                        useGlobalFrame=True)

#Create a torsional spring-damper between the rigid body and ground.
mbs.CreateTorsionalSpringDamper(bodyNumbers=[oGround, oBody],
                                position=[0,0,0], 
                                axis=[0,0,1],        
                                stiffness=2000,
                                damping=8,
                                useGlobalFrame=True)

#Applies a 3D torque to the rigid body.
mbs.CreateTorque(bodyNumber=oBody, loadVector=[0,0,0.8]) 

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


