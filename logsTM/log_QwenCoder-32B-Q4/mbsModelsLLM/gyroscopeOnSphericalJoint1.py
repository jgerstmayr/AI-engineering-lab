# ** given model description: **
# A gyro is modelled with a rigid body and a spherical joint. The gyro is
# modelled as cylindrical disc with mass m = 15 kg, disc radius r = 0.2 m, and disc
# width w = 0.04. The axis of the disc is initially oriented along positive x-axis
# and the disc is positioned at [0.25,0,0] (which is also the COM). The disc
# is connected to ground with a spherical joint at position [0,0,0]. The initial
# angular velocity of the disc is [200,0,0]. Gravity g = 11.15 m/s^2 acts in negative
# z-direction, and no further forces or damping are applied.
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
outerRadius = 0.2
length = 0.04
volume = np.pi * outerRadius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=outerRadius, axis=0)

#create a free rigid body using the defined inertia properties and applies gravity (z-direction).
oBody = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0.25,0,0], #reference position x/y/z of COM
                            initialVelocity=[0,0,0],   #optional
                            initialAngularVelocity=[200,0,0], #optional
                            gravity=[0,0,-11.15])       #optional

#Create a spherical joint between two bodies/ground
mbs.CreateSphericalJoint(bodyNumbers=[oGround, oBody],
                         position=[0,0,0], #global position of joint (in reference configuration)
                         constrainedAxes=[1,1,1]) #x,y,z directions: 1 = fixed, 0 = free motion

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 10
stepSize = 0.0005 #for large rotation speeds

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 5e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 1e-2
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.general.drawCoordinateSystem = False
SC.visualizationSettings.general.drawWorldBasis = True

#start solver:
mbs.SolveDynamic(simulationSettings)

