# ** given model description: **
# A rotor is modelled with a rigid body mounted on ground with Cartesian
# spring-dampers. The rotor is modelled as cylinder with mass m = 5 kg, disc radius r = 0.15
# m, and length = 0.5 m. The axis of the rotor is initially oriented along the
# x-axis and the reference point of the rotor lies at [0,0,0] (which is also the
# COM). The rotor is connected to ground with two Cartesian spring-dampers at global
# position [-0.5/2,0,0] resp. [0.5/2,0,0], the positions being identical with the
# local positions of the spring-dampers on the rotor. The Cartesian spring-dampers
# have stiffness values [1250,2000,2000] N/m and damping values [7.5,10,10] Ns/m.
# The initial angular velocity of the rotor is [300,0,0]. Gravity g = 9.81 m/s^2
# acts in negative y-direction, and no further forces or damping are applied.
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
mass = 5 
outerRadius = 0.15
length = 0.5
volume = np.pi * outerRadius**2 * length
inertiaCylinder = InertiaCylinder(density=mass/volume, length=length, outerRadius=outerRadius, axis=0)

#create a free rigid body using the defined inertia properties and applies gravity (y-direction).
oBody = mbs.CreateRigidBody(inertia=inertiaCylinder,
                            referencePosition=[0,0,0], 
                            initialVelocity=[0,0,0],   
                            initialAngularVelocity=[300,0,0], 
                            gravity=[0,-9.81,0])       

#Create a special spring-damper which acts on translations in global x, y, and z-direction, with possibility to connect rigid bodies, mass points together or on ground.
mbs.CreateCartesianSpringDamper(
    bodyNumbers=[oGround, oBody], 
    localPosition0=[-0.5/2,0,0], 
    localPosition1=[-0.5/2,0,0],        
    stiffness = [1250,2000,2000], 
    damping = [7.5,10,10], 
)

mbs.CreateCartesianSpringDamper(
    bodyNumbers=[oGround, oBody], 
    localPosition0=[0.5/2,0,0], 
    localPosition1=[0.5/2,0,0],        
    stiffness = [1250,2000,2000], 
    damping = [7.5,10,10], 
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

