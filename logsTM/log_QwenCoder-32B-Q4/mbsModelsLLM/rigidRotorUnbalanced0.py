# ** given model description: **
# A rotor is modelled with a rigid body mounted on ground with Cartesian
# spring-dampers. The rotor is modelled as cylinder with mass m = 3 kg, disc radius r = 0.12
# m, and length = 1 m. The axis of the rotor is initially oriented along the
# x-axis and the reference point of the rotor lies at [0,0,0]. The COM of the rigid
# body lies at [0,0.002,0], representing an unbalance U=3*0.002 kgm. The rotor
# is connected to ground with two Cartesian spring-dampers at global position
# [-1/2,0,0] resp. [1/2,0,0], the positions being identical with the local positions
# of the spring-dampers on the rotor. The Cartesian spring-dampers have stiffness
# values [1250,4000,4000] N/m and damping values [5,15,15] Ns/m. The rotor starts
# from zero velocity, and is driven by a torque [1,0,0] Nm. Gravity g = 3.73 m/s^2
# acts in negative y-direction. Simulate the rotor for 2s and use a stepSize of
# 0.2ms to meet the accuracy limits.
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
mass = 3 
outerRadius = 0.12
length = 1
volume = np.pi * outerRadius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=outerRadius, axis=0)
inertiaCylinder = inertiaCylinder.Translated([0,0.002,0]) #translate COM (in body-frame)

#create a free rigid body using the defined inertia properties and applies gravity (y-direction).
oBody = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0,0,0], #reference position x/y/z of COM
                            initialVelocity=[0,0,0],   #optional
                            initialAngularVelocity=[0,0,0], #optional
                            gravity=[0,-3.73,0])       #optional

#Applies a 3D torque to a rigid body.
#torque of 1Nm around the x-axis:
mbs.CreateTorque(bodyNumber=oBody, loadVector=[1,0,0]) #torque of 1Nm around x-axis

#Create a special spring-damper which acts on translations in global x, y, and z-direction, with possibility to connect rigid bodies, mass points together or on ground.
mbs.CreateCartesianSpringDamper(
    bodyNumbers=[oGround, oBody], #[body0,body1]
    localPosition0=[-0.5,0,0], #for body0
    localPosition1=[-0.5,0,0],        #for body1
    stiffness = [1250,4000,4000], #x,y,z stiffness
    damping = [5,15,15], #x,y,z damping
)

mbs.CreateCartesianSpringDamper(
    bodyNumbers=[oGround, oBody], #[body0,body1]
    localPosition0=[0.5,0,0], #for body0
    localPosition1=[0.5,0,0],        #for body1
    stiffness = [1250,4000,4000], #x,y,z stiffness
    damping = [5,15,15], #x,y,z damping
)

#Assemble has to be called just before solving or system analysis (after AddSensor!).
mbs.Assemble()

tEnd = 2
stepSize = 0.0002 #for large rotation speeds

simulationSettings = exu.SimulationSettings()
simulationSettings.solutionSettings.solutionWritePeriod = 2e-1
simulationSettings.solutionSettings.sensorsWritePeriod = 5e-3
simulationSettings.timeIntegration.numberOfSteps = int(tEnd/stepSize) #must be integer
simulationSettings.timeIntegration.endTime = tEnd
# simulationSettings.timeIntegration.verboseMode = 1

SC.visualizationSettings.nodes.drawNodesAsPoint=False
SC.visualizationSettings.nodes.defaultSize=1
SC.visualizationSettings.openGL.lineWidth = 3
SC.visualizationSettings.general.drawCoordinateSystem = False
SC.visualizationSettings.general.drawWorldBasis = True

#start solver:
mbs.SolveDynamic(simulationSettings)

